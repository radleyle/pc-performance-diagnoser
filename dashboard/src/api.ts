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
    source?: string;
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

  export type StorageScanMeta = {
    cached_at: number;
    from_cache: boolean;
    stale: boolean;
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
    frozen?: boolean;
  };

  export type SlowNowReport = {
    generated_at: number;
    window_minutes: number;
    status: "ok" | "warning" | "critical";
    headline: string;
    likely_causes: string[];
    metrics: { cpu_percent: number; cpu_delta: number; ram_used_percent: number };
    top_movers: {
      app_name: string;
      memory_mb: number;
      cpu_percent: number;
      memory_delta_mb: number;
    }[];
    issues: Issue[];
    startup_item_count: number;
    network: { status: string; message: string };
  };

  export type AppImpact = {
    app_name: string;
    impact_score: number;
    avg_memory_mb: number;
    peak_memory_mb: number;
    avg_cpu_percent: number;
    snapshot_count: number;
  };

  export type WeeklyDigest = {
    generated_at: number;
    days: number;
    diagnosis_counts: { warning: number; critical: number };
    averages: { cpu_percent: number | null; ram_used_percent: number | null };
    disk_free_gb: { start: number | null; end: number | null };
    top_apps: AppImpact[];
    smart_scans: number;
  };

  export type DuplicateGroup = {
    name: string;
    size_mb: number;
    count: number;
    waste_mb: number;
    files: { name: string; path: string; size_mb: number }[];
  };

  export type DevJunkItem = {
    name: string;
    path: string;
    category: string;
    size_mb: number;
  };

  export type FolderGrowthItem = {
    name: string;
    path: string;
    size_gb: number;
    delta_gb: number;
    has_history: boolean;
  };

  export type SystemHint = {
    name: string;
    path: string;
    size_gb: number | null;
    hint: string;
  };

  export type BaselineComparison = {
    metric: string;
    current: number;
    baseline_p95: number;
    delta: number;
    abnormal: boolean;
  };

  export function fetchSlowNowReport(minutes = 5) {
    return fetchJson<SlowNowReport>(`/report/slow-now?minutes=${minutes}`);
  }

  export function fetchWeeklyDigest() {
    return fetchJson<WeeklyDigest>("/digest/weekly");
  }

  export function fetchAppImpact(minutes = 60) {
    return fetchJson<{ count: number; data: AppImpact[] }>(
      `/processes/impact?minutes=${minutes}`,
    );
  }

  export function fetchNetworkStatus() {
    return fetchJson<{
      status: string;
      message: string;
      dns_latency_ms: number | null;
      ping_latency_ms: number | null;
    }>("/network/status");
  }

  export function fetchBaselineCompare() {
    return fetchJson<{ comparisons: BaselineComparison[] }>("/baseline/compare");
  }

  export function fetchFolderGrowth(days = 7) {
    return fetchJson<{ count: number; data: FolderGrowthItem[] }>(
      `/storage/folder-growth?days=${days}`,
    );
  }

  export function fetchDuplicates(minMb = 10, refresh = false) {
    return fetchJson<{ count: number; data: DuplicateGroup[] } & StorageScanMeta>(
      `/storage/duplicates?min_mb=${minMb}&refresh=${refresh}`,
    );
  }

  export function fetchDevJunk(refresh = false) {
    return fetchJson<{ count: number; data: DevJunkItem[] } & StorageScanMeta>(
      `/storage/dev-junk?refresh=${refresh}`,
    );
  }

  export function fetchSystemHints() {
    return fetchJson<{ count: number; data: SystemHint[] }>("/storage/system-hints");
  }

  export function fetchCleanupLog(limit = 10) {
    return fetchJson<{
      count: number;
      data: {
        id: number;
        timestamp: number;
        action_id: string;
        path: string;
        size_bytes: number;
        restored: number;
      }[];
    }>(`/cleanup/log?limit=${limit}`);
  }

  export function explainIssue(issue: Issue) {
    return fetchJson<{ explanation: string }>("/issues/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ issue }),
    });
  }

  export function fetchActionSuggestions() {
    return fetchJson<{ diagnosis: DiagnosisResponse; suggestions: string }>(
      "/actions/suggest",
      { method: "POST" },
    );
  }

  export function fetchBootAudit() {
    return fetchJson<{
      startup_item_count: number;
      startup_items: StartupItem[];
      heavy_apps: AppImpact[];
      message: string;
    }>("/boot-audit");
  }

  export function toggleStartupItem(path: string, enabled: boolean) {
    return fetchJson<{ ok: boolean; message: string }>("/startup-items/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path, enabled }),
    });
  }

  export function freezeProcess(pid: number) {
    return fetchJson<{ ok: boolean; message: string }>(
      `/processes/${pid}/freeze`,
      { method: "POST" },
    );
  }

  export function resumeProcess(pid: number) {
    return fetchJson<{ ok: boolean; message: string }>(
      `/processes/${pid}/resume`,
      { method: "POST" },
    );
  }

  export function quitAppGroup(appName: string) {
    return fetchJson<{ ok: boolean; message: string }>("/processes/quit-app", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ app_name: appName }),
    });
  }

  export function fetchStorageBreakdown(limit = 10, refresh = false) {
    return fetchJson<
      { count: number; data: FolderSize[] } & StorageScanMeta
    >(`/storage/breakdown?limit=${limit}&refresh=${refresh}`);
  }

  export function fetchLargeFiles(minMb = 500, limit = 15, refresh = false) {
    return fetchJson<
      { min_mb: number; count: number; data: LargeFile[] } & StorageScanMeta
    >(`/storage/large-files?min_mb=${minMb}&limit=${limit}&refresh=${refresh}`);
  }

  export function revealInFinder(path: string) {
    return fetchJson<{ ok: boolean; message: string }>("/storage/reveal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
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