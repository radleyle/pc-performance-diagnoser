import type { HealthResponse } from "./api";

type Props = {
  health: HealthResponse | null;
};

function StatusDot({ status }: { status: string }) {
  return <span className={`status-dot ${status}`} />;
}

export default function ServiceStatus({ health }: Props) {
  if (!health) {
    return <div className="service-status">Checking services...</div>;
  }

  return (
    <div className="service-status">
      <div className="service-item">
        <StatusDot status="ok" />
        <span>API</span>
      </div>

      <div className="service-item" title={health.collector.message}>
        <StatusDot status={health.collector.status} />
        <span>
          Collector
          {health.collector.seconds_ago != null &&
            ` (${health.collector.seconds_ago}s ago)`}
        </span>
      </div>

      <div className="service-item" title={health.ollama.message}>
        <StatusDot status={health.ollama.status} />
        <span>Ollama</span>
      </div>
    </div>
  );
}