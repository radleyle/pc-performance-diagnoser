import type { MetricPoint } from "./api";

type Props = {
  metrics: MetricPoint[];
};

export default function DiskPanel({ metrics }: Props) {
  const latest = [...metrics]
    .reverse()
    .find(
      (m) => m.disk_free_gb != null && m.disk_used_percent != null,
    );

  if (!latest) {
    return (
      <section className="panel">
        <h2>Disk space</h2>
        <p className="muted">
          No disk data yet — stop the collector (Ctrl+C) and start it again:
          python -m collector.main
        </p>
      </section>
    );
  }

  const usedPercent = latest.disk_used_percent;
  const freeGb = latest.disk_free_gb;

  let barClass = "ok";
  if (usedPercent > 90 || freeGb < 2) barClass = "critical";
  else if (usedPercent > 80 || freeGb < 10) barClass = "warning";

  return (
    <section className="panel">
      <h2>Disk space</h2>
      <p>
        <strong>{freeGb.toFixed(1)} GB</strong> free · {usedPercent.toFixed(1)}% used
      </p>
      <div className="disk-bar-track">
        <div
          className={`disk-bar-fill ${barClass}`}
          style={{ width: `${Math.min(usedPercent, 100)}%` }}
        />
      </div>
    </section>
  );
}