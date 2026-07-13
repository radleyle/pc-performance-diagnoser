const STORAGE_KEY = "pcdiagnoser-onboarded";

export function isOnboarded(): boolean {
  return localStorage.getItem(STORAGE_KEY) === "true";
}

export function markOnboarded() {
  localStorage.setItem(STORAGE_KEY, "true");
}
