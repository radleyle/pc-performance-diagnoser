const API_BASE = "http://127.0.0.1:8000";

export type HealthResponse = {
  status: string;
  service: string;
};

export type MetricPoint = {
  timestamp: number;
  cpu_percent: number;
  ram_available_mb: number;
  ram_used_percent: number;
};

export type ProcessRow = {
  process_name: string;
  memory_mb: number;
  cpu_percent: number | null;
  timestamp: number;
};

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    throw new Error(`API error ${response.status} on ${path}`);
  }

  return response.json() as Promise<T>;
}

export function fetchHealth(): Promise<HealthResponse> {
  return fetchJson<HealthResponse>("/health");
}

export function fetchMetrics(minutes = 60): Promise<{
  minutes: number;
  count: number;
  data: MetricPoint[];
}> {
  return fetchJson(`/metrics?minutes=${minutes}`);
}

export function fetchProcesses(): Promise<{
  count: number;
  data: ProcessRow[];
}> {
  return fetchJson("/processes");
}

export type Issue = {
    type: string;
    severity: "high" | "medium";
    message: string;
    evidence: Record<string, unknown>;
  };
  
  export type DiagnosisResponse = {
    status: "ok" | "warning" | "critical";
    issues: Issue[];
    top_processes: { name: string; memory_mb: number }[];
  };
  
  export function fetchDiagnose(): Promise<DiagnosisResponse> {
    return fetchJson<DiagnosisResponse>("/diagnose", { method: "POST" });
  }

  export type AnalyzeResponse = {
    status: "ok" | "warning" | "critical";
    issues: Issue[];
    top_processes: { name: string; memory_mb: number }[];
    explanation: string;
  };
  
  export function fetchAnalyze(): Promise<AnalyzeResponse> {
    return fetchJson<AnalyzeResponse>("/analyze", { method: "POST" });
  }