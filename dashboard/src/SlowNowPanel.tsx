import { useEffect, useState } from "react";
import { fetchSlowNowReport, type SlowNowReport } from "./api";
import PanelShell from "./PanelShell";

export default function SlowNowPanel() {
  const [report, setReport] = useState<SlowNowReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchSlowNowReport()
      .then((data) => {
        if (!cancelled) {
          setReport(data);
          setError("");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load report");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <PanelShell
      title="Why slow now?"
      description="One-click snapshot of the last few minutes."
      className="slow-now-panel"
      defaultOpen
    >
      {loading && <p className="muted">Building report...</p>}
      {error && <p className="error">{error}</p>}
      {report && (
        <div className="slow-now-layout">
          <div className="slow-now-summary">
            <p className={`badge ${report.status}`}>{report.headline}</p>

            <div className="slow-metrics">
              <div className="slow-metric-card">
                <span className="slow-metric-label">CPU</span>
                <span className="slow-metric-value">{report.metrics.cpu_percent}%</span>
              </div>
              <div className="slow-metric-card">
                <span className="slow-metric-label">RAM</span>
                <span className="slow-metric-value">
                  {report.metrics.ram_used_percent}%
                </span>
              </div>
              <div className="slow-metric-card">
                <span className="slow-metric-label">Δ CPU</span>
                <span className="slow-metric-value">{report.metrics.cpu_delta}%</span>
              </div>
            </div>

            <ul className="cause-list cause-list-grid">
              {report.likely_causes.map((cause) => (
                <li key={cause}>{cause}</li>
              ))}
            </ul>
          </div>

          {report.top_movers.length > 0 && (
            <div className="slow-now-movers">
              <h3 className="slow-now-subtitle">Top movers</h3>
              <table className="slow-movers-table">
                <thead>
                  <tr>
                    <th>Process</th>
                    <th>Memory</th>
                    <th>Change</th>
                  </tr>
                </thead>
                <tbody>
                  {report.top_movers.map((mover) => (
                    <tr key={mover.app_name}>
                      <td>{mover.app_name}</td>
                      <td>{mover.memory_mb} MB</td>
                      <td
                        className={
                          mover.memory_delta_mb > 0
                            ? "delta-up"
                            : mover.memory_delta_mb < 0
                              ? "delta-down"
                              : "delta-neutral"
                        }
                      >
                        {mover.memory_delta_mb > 0 ? "+" : ""}
                        {mover.memory_delta_mb} MB
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </PanelShell>
  );
}
