import { useEffect, useRef } from "react";
import type { DiagnosisResponse } from "./api";

function buildNotificationBody(diagnosis: DiagnosisResponse): string {
  if (diagnosis.issues.length === 0) {
    return "System status is critical.";
  }
  return diagnosis.issues
    .slice(0, 3)
    .map((issue) => issue.message)
    .join(" · ");
}

export function useCriticalNotifications(
  diagnosis: DiagnosisResponse | null,
  enabled: boolean,
) {
  const previousStatus = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled || !diagnosis || diagnosis.status !== "critical") {
      if (diagnosis) {
        previousStatus.current = diagnosis.status;
      }
      return;
    }

    if (previousStatus.current === "critical") {
      return;
    }

    previousStatus.current = diagnosis.status;

    if (!("Notification" in window)) {
      return;
    }

    const show = () => {
      new Notification("PC Performance Diagnoser — Critical", {
        body: buildNotificationBody(diagnosis),
      });
    };

    if (Notification.permission === "granted") {
      show();
      return;
    }

    if (Notification.permission !== "denied") {
      Notification.requestPermission().then((permission) => {
        if (permission === "granted") {
          show();
        }
      });
    }
  }, [diagnosis, enabled]);
}

export function requestNotificationPermission() {
  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }
}
