import type { ComparisonSummary } from "./api";

type Props = {
  summary: ComparisonSummary | null;
};

function formatDelta(value: number | null | undefined, unit: string): string {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value}${unit}`;
}

function deltaClass(value: number | null | undefined): string {
  if (value == null) return "delta-neutral";
  if (value > 0) return "delta-up";
  if (value < 0) return "delta-down";
  return "delta-neutral";
}

export default function WhatChangedPanel({ summary }: Props) {
  if (!summary) {
    return (
      <section className="panel">
        <h2>What changed? (1h)</h2>
        <p className="muted">Loading comparison...</p>
      </section>
    );
  }

  const { current, past, delta, current_top_process, past_top_process } = summary;

  if (!current || !past) {
    return (
      <section className="panel">
        <h2>What changed? (1h)</h2>
        <p className="muted">
          Not enough history yet — leave the collector running for an hour.
        </p>
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>What changed? (1h)</h2>
      <div className="comparison-grid">
        <div className="comparison-row">
          <span className="comparison-label">CPU</span>
          <span>{current.cpu_percent.toFixed(1)}%</span>
          <span className="muted">was {past.cpu_percent.toFixed(1)}%</span>
          <span className={deltaClass(delta?.cpu_percent)}>
            {formatDelta(delta?.cpu_percent, "%")}
          </span>
        </div>

        <div className="comparison-row">
          <span className="comparison-label">RAM free</span>
          <span>{current.ram_available_mb.toFixed(0)} MB</span>
          <span className="muted">was {past.ram_available_mb.toFixed(0)} MB</span>
          <span className={deltaClass(delta?.ram_available_mb)}>
            {formatDelta(delta?.ram_available_mb, " MB")}
          </span>
        </div>

        {current.disk_free_gb != null && past.disk_free_gb != null && (
          <div className="comparison-row">
            <span className="comparison-label">Disk free</span>
            <span>{current.disk_free_gb.toFixed(1)} GB</span>
            <span className="muted">was {past.disk_free_gb.toFixed(1)} GB</span>
            <span className={deltaClass(delta?.disk_free_gb)}>
              {formatDelta(delta?.disk_free_gb, " GB")}
            </span>
          </div>
        )}

        <div className="comparison-row">
          <span className="comparison-label">Top process</span>
          <span>{current_top_process?.app_name ?? "—"}</span>
          <span className="muted">
            was {past_top_process?.app_name ?? "—"}
          </span>
          <span className="muted">
            {current_top_process
              ? `${current_top_process.memory_mb.toFixed(0)} MB`
              : ""}
          </span>
        </div>
      </div>
    </section>
  );
}
