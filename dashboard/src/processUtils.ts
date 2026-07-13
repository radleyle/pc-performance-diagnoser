export function normalizeAppName(processName: string): string {
  if (processName.includes(" Helper")) {
    return processName.split(" Helper")[0].trim();
  }
  return processName.trim();
}
