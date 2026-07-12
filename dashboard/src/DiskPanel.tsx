import type { CSSProperties } from "react";
import type { MetricPoint } from "./api";
import PanelShell from "./PanelShell";

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
      <PanelShell title="Storage" collapsible defaultOpen>
        <p className="muted">No disk data yet — restart the collector.</p>
      </PanelShell>
    );
  }

  const usedPercent = latest.disk_used_percent!;
  const freeGb = latest.disk_free_gb!;

  let barClass = "ok";
  let diskColor = "var(--green)";
  if (usedPercent > 90 || freeGb < 2) {
    barClass = "critical";
    diskColor = "var(--red)";
  } else if (usedPercent > 80 || freeGb < 10) {
    barClass = "warning";
    diskColor = "var(--amber)";
  }

  return (
    <PanelShell title="Storage" collapsible defaultOpen>
      <div className="disk-panel-content">
        <div
          className="disk-ring"
          style={
            {
              "--disk-pct": usedPercent,
              "--disk-color": diskColor,
            } as CSSProperties
          }
        >
          <span className="disk-ring-label">{usedPercent.toFixed(0)}%</span>
        </div>

        <div className="disk-details">
          <p>
            <strong>{freeGb.toFixed(1)} GB</strong>{" "}
            <span className="muted">free</span>
          </p>
          <p className="panel-desc">{usedPercent.toFixed(1)}% of disk in use</p>
        </div>
      </div>

      <div className="disk-bar-track">
        <div
          className={`disk-bar-fill ${barClass}`}
          style={{ width: `${Math.min(usedPercent, 100)}%` }}
        />
      </div>
    </PanelShell>
  );
}
