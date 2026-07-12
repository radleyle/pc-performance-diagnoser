import { useEffect, useRef } from "react";
import { isTauri } from "@tauri-apps/api/core";
import {
  isPermissionGranted,
  requestPermission,
  sendNotification,
} from "@tauri-apps/plugin-notification";
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

async function showNativeNotification(body: string) {
  if (isTauri()) {
    let granted = await isPermissionGranted();
    if (!granted) {
      const permission = await requestPermission();
      granted = permission === "granted";
    }
    if (granted) {
      await sendNotification({
        title: "PC Performance Diagnoser — Critical",
        body,
      });
    }
    return;
  }

  if (!("Notification" in window)) return;

  const show = () => {
    new Notification("PC Performance Diagnoser — Critical", { body });
  };

  if (Notification.permission === "granted") {
    show();
    return;
  }

  if (Notification.permission !== "denied") {
    Notification.requestPermission().then((permission) => {
      if (permission === "granted") show();
    });
  }
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
    void showNativeNotification(buildNotificationBody(diagnosis));
  }, [diagnosis, enabled]);
}

export function requestNotificationPermission() {
  if (isTauri()) {
    void isPermissionGranted().then(async (granted) => {
      if (!granted) await requestPermission();
    });
    return;
  }

  if ("Notification" in window && Notification.permission === "default") {
    Notification.requestPermission();
  }
}
