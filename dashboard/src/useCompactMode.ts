const STORAGE_KEY = "pcdiagnoser-compact-mode";

export function loadCompactMode(): boolean {
  return localStorage.getItem(STORAGE_KEY) === "true";
}

export function saveCompactMode(enabled: boolean) {
  localStorage.setItem(STORAGE_KEY, String(enabled));
}
