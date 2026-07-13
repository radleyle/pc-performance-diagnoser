import { useEffect, useRef } from "react";
import { isTauri } from "@tauri-apps/api/core";
import {
  isPermissionGranted,
  requestPermission,
  sendNotification,
} from "@tauri-apps/plugin-notification";
import type { DiagnosisResponse } from "./api";

export type AlertLevel = "off" | "critical" | "all";

const STORAGE_KEY = "pcdiagnoser-alert-level";

export function loadAlertLevel(): AlertLevel {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "off" || saved === "critical" || saved === "all") {
    return saved;
  }
  return "all";
}

export function saveAlertLevel(level: AlertLevel) {
  localStorage.setItem(STORAGE_KEY, level);
}

function shouldNotify(level: AlertLevel, status: string): boolean {
  if (level === "off") return false;
  if (status === "critical") return true;
  if (level === "all" && status === "warning") return true;
  return false;
}

function notificationTitle(status: string): string {
  if (status === "critical") {
    return "PC Performance Diagnoser — Critical";
  }
  return "PC Performance Diagnoser — Warning";
}

function buildNotificationBody(diagnosis: DiagnosisResponse): string {
  if (diagnosis.issues.length === 0) {
    return `System status is ${diagnosis.status}.`;
  }
  return diagnosis.issues
    .slice(0, 3)
    .map((issue) => issue.message)
    .join(" · ");
}

async function showNativeNotification(title: string, body: string) {
  if (isTauri()) {
    let granted = await isPermissionGranted();
    if (!granted) {
      const permission = await requestPermission();
      granted = permission === "granted";
    }
    if (granted) {
      await sendNotification({ title, body });
    }
    return;
  }

  if (!("Notification" in window)) return;

  const show = () => {
    new Notification(title, { body });
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

export function useStatusNotifications(
  diagnosis: DiagnosisResponse | null,
  alertLevel: AlertLevel,
) {
  const previousStatus = useRef<string | null>(null);

  useEffect(() => {
    if (!diagnosis || !shouldNotify(alertLevel, diagnosis.status)) {
      if (diagnosis) {
        previousStatus.current = diagnosis.status;
      }
      return;
    }

    if (previousStatus.current === diagnosis.status) {
      return;
    }

    previousStatus.current = diagnosis.status;
    void showNativeNotification(
      notificationTitle(diagnosis.status),
      buildNotificationBody(diagnosis),
    );
  }, [diagnosis, alertLevel]);
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
