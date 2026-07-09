import type { DiagnosisResponse } from "./api";

type Props = {
  diagnosis: DiagnosisResponse | null;
};

export default function AlertsPanel({ diagnosis }: Props) {
  if (!diagnosis) {
    return (
      <section className="panel">
        <h2>Alerts</h2>
        <p className="muted">Loading diagnosis...</p>
      </section>
    );
  }

  const statusClass =
    diagnosis.status === "critical"
      ? "badge critical"
      : diagnosis.status === "warning"
        ? "badge warning"
        : "badge ok";

  return (
    <section className="panel">
      <h2>Alerts</h2>
      <p>
        Status: <span className={statusClass}>{diagnosis.status}</span>
      </p>

      {diagnosis.issues.length === 0 ? (
        <p className="muted">No issues detected.</p>
      ) : (
        <ul className="issue-list">
          {diagnosis.issues.map((issue, index) => (
            <li key={`${issue.type}-${index}`} className={`issue ${issue.severity}`}>
              <strong>[{issue.severity}]</strong> {issue.message}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}