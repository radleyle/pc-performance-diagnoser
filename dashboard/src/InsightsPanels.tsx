import { useEffect, useState } from "react";
import {
  fetchWeeklyDigest,
  fetchNetworkStatus,
  fetchBaselineCompare,
  fetchBootAudit,
  fetchActionSuggestions,
  fetchAppImpact,
  type WeeklyDigest,
  type BaselineComparison,
} from "./api";
import PanelShell from "./PanelShell";

export function WeeklyDigestPanel() {
  const [digest, setDigest] = useState<WeeklyDigest | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWeeklyDigest()
      .then(setDigest)
      .finally(() => setLoading(false));
  }, []);

  return (
    <PanelShell title="Weekly digest" description="Last 7 days at a glance." collapsible>
      {loading && <p className="muted">Building digest...</p>}
      {digest && (
        <ul className="digest-list">
          <li>
            Warnings: <strong>{digest.diagnosis_counts.warning}</strong> · Critical:{" "}
            <strong>{digest.diagnosis_counts.critical}</strong>
          </li>
          {digest.averages.cpu_percent != null && (
            <li>Avg CPU: {digest.averages.cpu_percent}%</li>
          )}
          {digest.disk_free_gb.end != null && (
            <li>Disk free now: {digest.disk_free_gb.end} GB</li>
          )}
          {digest.top_apps[0] && (
            <li>Top impact app: {digest.top_apps[0].app_name}</li>
          )}
        </ul>
      )}
    </PanelShell>
  );
}

export function NetworkPanel() {
  const [status, setStatus] = useState<string>("");
  const [latency, setLatency] = useState<string>("");

  useEffect(() => {
    fetchNetworkStatus().then((res) => {
      setStatus(res.message);
      const ms = res.ping_latency_ms ?? res.dns_latency_ms;
      setLatency(ms != null ? `${ms} ms` : "n/a");
    });
  }, []);

  return (
    <PanelShell title="Network" description="DNS and ping latency check." collapsible>
      <p>{status || "Checking..."}</p>
      <p className="muted">Latency: {latency}</p>
    </PanelShell>
  );
}

export function BaselinePanel() {
  const [rows, setRows] = useState<BaselineComparison[]>([]);

  useEffect(() => {
    fetchBaselineCompare().then((res) => setRows(res.comparisons));
  }, []);

  return (
    <PanelShell title="Your baseline" description="Compared to your usual patterns." collapsible>
      {rows.length === 0 ? (
        <p className="muted">Learning baseline — needs more history.</p>
      ) : (
        <ul className="baseline-list">
          {rows.map((row) => (
            <li key={row.metric} className={row.abnormal ? "abnormal" : ""}>
              {row.metric}: {row.current} (usual p95 {row.baseline_p95})
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}

export function BootAuditPanel() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchBootAudit().then((res) => setMessage(res.message));
  }, []);

  return (
    <PanelShell title="Boot audit" description="Login items and heavy apps." collapsible defaultOpen={false}>
      <p>{message || "Loading..."}</p>
    </PanelShell>
  );
}

export function ActionSuggestionsPanel() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const res = await fetchActionSuggestions();
      setText(res.suggestions);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PanelShell title="Suggested actions" description="AI recommendations from current diagnosis." collapsible>
      <button type="button" className="ghost-btn" disabled={loading} onClick={load}>
        {loading ? "Thinking..." : "Get suggestions"}
      </button>
      {error && <p className="error">{error}</p>}
      {text && <p className="suggestions-text">{text}</p>}
    </PanelShell>
  );
}

export function ImpactPanel() {
  const [apps, setApps] = useState<{ app_name: string; impact_score: number }[]>([]);

  useEffect(() => {
    fetchAppImpact(60).then((res) => setApps(res.data));
  }, []);

  return (
    <PanelShell title="App impact" description="7-day weighted CPU + memory score." collapsible>
      {apps.length === 0 ? (
        <p className="muted">Collecting impact data...</p>
      ) : (
        <ul className="impact-list">
          {apps.map((app) => (
            <li key={app.app_name}>
              <strong>{app.app_name}</strong>
              <span>{app.impact_score}</span>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}
