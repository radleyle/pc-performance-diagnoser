import { useCallback, useEffect, useState } from "react";
import { fetchLiveProcesses, killProcess, type LiveProcess } from "./api";
import PanelShell from "./PanelShell";

export default function LiveProcessPanel() {
  const [processes, setProcesses] = useState<LiveProcess[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionPid, setActionPid] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await fetchLiveProcesses();
      setProcesses(res.data);
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

  async function handleKill(pid: number, name: string) {
    const ok = window.confirm(`Stop process "${name}" (PID ${pid})?`);
    if (!ok) return;

    setActionPid(pid);
    try {
      await killProcess(pid);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not stop process");
    } finally {
      setActionPid(null);
    }
  }

  const peak = processes[0]?.memory_mb ?? 1;

  return (
    <PanelShell
      title="Running processes"
      description="Live process list with stop action. Use with care."
      className="panel-full"
    >
      {loading && <p className="muted">Loading processes...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && processes.length === 0 && (
        <p className="muted">No process data.</p>
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
                <td>
                  <button
                    type="button"
                    className="kill-btn"
                    disabled={actionPid === proc.pid}
                    onClick={() => handleKill(proc.pid, proc.process_name)}
                  >
                    {actionPid === proc.pid ? "..." : "Stop"}
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
