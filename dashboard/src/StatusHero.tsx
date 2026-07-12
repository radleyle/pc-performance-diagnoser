import type { DiagnosisResponse, MetricPoint } from "./api";

type Props = {
  diagnosis: DiagnosisResponse | null;
  metrics: MetricPoint[];
};

function latestMetric(metrics: MetricPoint[]) {
  return metrics.length > 0 ? metrics[metrics.length - 1] : null;
}

function statusHeadline(status: string | undefined): string {
  if (status === "critical") return "Needs attention";
  if (status === "warning") return "A few things to watch";
  return "Your system looks healthy";
}

function statusSubtext(status: string | undefined, issueCount: number): string {
  if (status === "critical") {
    return `${issueCount} critical issue${issueCount === 1 ? "" : "s"} detected`;
  }
  if (status === "warning") {
    return `${issueCount} warning${issueCount === 1 ? "" : "s"} active`;
  }
  return "CPU, memory, and disk are within normal ranges";
}

export default function StatusHero({ diagnosis, metrics }: Props) {
  const latest = latestMetric(metrics);
  const status = diagnosis?.status ?? "ok";
  const issueCount = diagnosis?.issues.length ?? 0;

  return (
    <section className={`hero-panel status-${status}`}>
      <div className="hero-main">
        <div className={`status-orb status-orb-${status}`} aria-hidden="true">
          <div className="status-orb-inner">
            {status === "ok" && <span className="status-icon">✓</span>}
            {status === "warning" && <span className="status-icon">!</span>}
            {status === "critical" && <span className="status-icon">!</span>}
          </div>
        </div>

        <div className="hero-copy">
          <p className="hero-eyebrow">System status</p>
          <h2 className="hero-title">{statusHeadline(status)}</h2>
          <p className="hero-subtitle">{statusSubtext(status, issueCount)}</p>
        </div>
      </div>

      {latest && (
        <div className="stat-cards">
          <div className="stat-card">
            <span className="stat-label">CPU</span>
            <span className="stat-value">{latest.cpu_percent.toFixed(1)}%</span>
            <span className="stat-hint">current load</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">RAM free</span>
            <span className="stat-value">
              {Math.round(latest.ram_available_mb).toLocaleString()}
              <span className="stat-unit">MB</span>
            </span>
            <span className="stat-hint">{latest.ram_used_percent.toFixed(1)}% used</span>
          </div>

          <div className="stat-card">
            <span className="stat-label">Disk free</span>
            <span className="stat-value">
              {latest.disk_free_gb != null ? (
                <>
                  {latest.disk_free_gb.toFixed(1)}
                  <span className="stat-unit">GB</span>
                </>
              ) : (
                "—"
              )}
            </span>
            <span className="stat-hint">
              {latest.disk_used_percent != null
                ? `${latest.disk_used_percent.toFixed(1)}% used`
                : "collecting"}
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
