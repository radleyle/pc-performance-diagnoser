const API_BASE = "http://127.0.0.1:8000";

export type ServiceStatus = "ok" | "stale" | "down";

export type HealthResponse = {
  api: string;
  collector: {
    status: ServiceStatus;
    last_snapshot_ms: number | null;
    seconds_ago: number | null;
    message: string;
  };
  ollama: {
    status: ServiceStatus;
    message: string;
    models_available: number;
  };
};

export type MetricPoint = {
    timestamp: number;
    cpu_percent: number;
    ram_available_mb: number;
    ram_used_percent: number;
    disk_free_gb?: number | null;
    disk_used_percent?: number | null;
};

export type ProcessRow = {
    app_name: string;
    memory_mb: number;
    cpu_percent: number;
    process_count: number;
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
    grouped: boolean;
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

  export type DiagnosisHistoryItem = {
    id: number;
    timestamp: number;
    status: "ok" | "warning" | "critical" | "unknown";
    issue_count: number;
    explanation: string | null;
  };
  
  export function fetchDiagnosisHistory(
    limit = 20
  ): Promise<{ count: number; data: DiagnosisHistoryItem[] }> {
    return fetchJson(`/diagnoses?limit=${limit}`);
  }

  export type MetricSnapshot = {
    timestamp: number;
    cpu_percent: number;
    ram_available_mb: number;
    ram_used_percent: number;
    disk_free_gb: number | null;
    disk_used_percent: number | null;
  };

  export type ProcessSnapshot = {
    app_name: string;
    memory_mb: number;
    cpu_percent: number;
  };

  export type ComparisonSummary = {
    minutes_ago: number;
    current: MetricSnapshot | null;
    past: MetricSnapshot | null;
    delta: {
      cpu_percent: number | null;
      ram_available_mb: number | null;
      ram_used_percent: number | null;
      disk_free_gb: number | null;
      disk_used_percent: number | null;
    } | null;
    current_top_process: ProcessSnapshot | null;
    past_top_process: ProcessSnapshot | null;
  };

  export function fetchSummary(
    minutesAgo = 60
  ): Promise<ComparisonSummary> {
    return fetchJson(`/summary?minutes_ago=${minutesAgo}`);
  }

  export type ReportResponse = {
    generated_at: number;
    diagnosis: DiagnosisResponse;
    comparison: ComparisonSummary;
    top_processes: ProcessRow[];
  };

  export function fetchReport(): Promise<ReportResponse> {
    return fetchJson("/report");
  }

  export type FolderSize = {
    name: string;
    path: string;
    size_bytes: number;
    size_gb: number;
  };

  export type LargeFile = {
    name: string;
    path: string;
    size_bytes: number;
    size_mb: number;
  };

  export type CleanupAction = {
    id: string;
    label: string;
    description: string;
    size_bytes: number;
    size_mb: number;
    available: boolean;
  };

  export type CleanupPreview = {
    actions: CleanupAction[];
    total_reclaimable_bytes: number;
    total_reclaimable_mb: number;
  };

  export type StartupItem = {
    name: string;
    path: string;
    location: string;
    enabled: boolean;
  };

  export type LiveProcess = {
    pid: number;
    process_name: string;
    memory_mb: number;
    cpu_percent: number;
  };

  export function fetchStorageBreakdown(limit = 10) {
    return fetchJson<{ count: number; data: FolderSize[] }>(
      `/storage/breakdown?limit=${limit}`,
    );
  }

  export function fetchLargeFiles(minMb = 500, limit = 15) {
    return fetchJson<{ min_mb: number; count: number; data: LargeFile[] }>(
      `/storage/large-files?min_mb=${minMb}&limit=${limit}`,
    );
  }

  export function fetchCleanupPreview() {
    return fetchJson<CleanupPreview>("/cleanup/preview");
  }

  export function runCleanup(actionIds: string[]) {
    return fetchJson<{ results: { id: string; ok: boolean; message: string }[] }>(
      "/cleanup/run",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_ids: actionIds }),
      },
    );
  }

  export function fetchStartupItems() {
    return fetchJson<{ count: number; data: StartupItem[] }>("/startup-items");
  }

  export function fetchLiveProcesses(limit = 25) {
    return fetchJson<{ count: number; data: LiveProcess[] }>(
      `/processes/live?limit=${limit}`,
    );
  }

  export function killProcess(pid: number) {
    return fetchJson<{ ok: boolean; message: string }>(
      `/processes/${pid}/kill`,
      { method: "POST" },
    );
  }