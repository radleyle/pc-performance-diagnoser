import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchAppImpact,
  fetchLiveProcesses,
  freezeProcess,
  killProcess,
  quitAppGroup,
  resumeProcess,
  type AppImpact,
  type LiveProcess,
} from "./api";
import PanelShell from "./PanelShell";
import { normalizeAppName } from "./processUtils";

export default function LiveProcessPanel() {
  const [processes, setProcesses] = useState<LiveProcess[]>([]);
  const [impact, setImpact] = useState<AppImpact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionPid, setActionPid] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [procRes, impactRes] = await Promise.all([
        fetchLiveProcesses(),
        fetchAppImpact(60),
      ]);
      setProcesses(procRes.data);
      setImpact(impactRes.data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load processes");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [load]);

  const impactByApp = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of impact) map.set(row.app_name, row.impact_score);
    return map;
  }, [impact]);

  const groupedApps = useMemo(() => {
    const groups = new Map<string, LiveProcess[]>();
    for (const proc of processes) {
      const app = normalizeAppName(proc.process_name);
      const list = groups.get(app) ?? [];
      list.push(proc);
      groups.set(app, list);
    }
    return [...groups.entries()].sort(
      (a, b) =>
        b[1].reduce((sum, p) => sum + p.memory_mb, 0) -
        a[1].reduce((sum, p) => sum + p.memory_mb, 0),
    );
  }, [processes]);

  async function runAction(fn: () => Promise<unknown>) {
    try {
      await fn();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    }
  }

  const peak = processes[0]?.memory_mb ?? 1;

  return (
    <PanelShell
      title="Running processes"
      description="Live list with pause, stop, and quit-all actions."
      className="panel-full"
    >
      {loading && <p className="muted">Loading processes...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && groupedApps.length > 0 && (
        <div className="process-groups">
          {groupedApps.slice(0, 8).map(([appName]) => (
            <div key={appName} className="process-group-card">
              <div className="file-row">
                <strong>{appName}</strong>
                <span className="muted">
                  impact {impactByApp.get(appName) ?? "—"}
                </span>
              </div>
              <button
                type="button"
                className="ghost-btn"
                onClick={() =>
                  runAction(() => {
                    const ok = window.confirm(`Quit all processes for ${appName}?`);
                    if (!ok) return Promise.resolve();
                    return quitAppGroup(appName);
                  })
                }
              >
                Quit all
              </button>
            </div>
          ))}
        </div>
      )}
      {!loading && processes.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Process</th>
              <th>PID</th>
              <th>Memory</th>
              <th>CPU</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {processes.map((proc) => (
              <tr key={proc.pid}>
                <td>{proc.process_name}</td>
                <td>{proc.pid}</td>
                <td>
                  <div className="memory-cell">
                    <span>{Math.round(proc.memory_mb)} MB</span>
                    <div className="memory-bar-track">
                      <div
                        className="memory-bar-fill"
                        style={{
                          width: `${Math.min((proc.memory_mb / peak) * 100, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </td>
                <td>{proc.cpu_percent.toFixed(1)}%</td>
                <td className="process-actions">
                  {proc.frozen ? (
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={actionPid === proc.pid}
                      onClick={() => {
                        setActionPid(proc.pid);
                        runAction(() => resumeProcess(proc.pid)).finally(() =>
                          setActionPid(null),
                        );
                      }}
                    >
                      Resume
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="ghost-btn"
                      disabled={actionPid === proc.pid}
                      onClick={() => {
                        setActionPid(proc.pid);
                        runAction(() => freezeProcess(proc.pid)).finally(() =>
                          setActionPid(null),
                        );
                      }}
                    >
                      Pause
                    </button>
                  )}
                  <button
                    type="button"
                    className="kill-btn"
                    disabled={actionPid === proc.pid}
                    onClick={() => {
                      const ok = window.confirm(
                        `Stop "${proc.process_name}" (PID ${proc.pid})?`,
                      );
                      if (!ok) return;
                      setActionPid(proc.pid);
                      runAction(() => killProcess(proc.pid)).finally(() =>
                        setActionPid(null),
                      );
                    }}
                  >
                    Stop
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PanelShell>
  );
}
