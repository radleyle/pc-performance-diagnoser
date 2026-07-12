import type { DiagnosisResponse } from "./api";
import PanelShell from "./PanelShell";

type Props = {
  diagnosis: DiagnosisResponse | null;
};

export default function AlertsPanel({ diagnosis }: Props) {
  if (!diagnosis) {
    return (
      <PanelShell title="Alerts" collapsible defaultOpen>
        <p className="muted">Loading diagnosis...</p>
      </PanelShell>
    );
  }

  const statusClass =
    diagnosis.status === "critical"
      ? "badge critical"
      : diagnosis.status === "warning"
        ? "badge warning"
        : "badge ok";

  return (
    <PanelShell title="Alerts" collapsible defaultOpen>
      <div className="alerts-status-row">
        <span className="muted">Status</span>
        <span className={statusClass}>{diagnosis.status}</span>
      </div>

      {diagnosis.issues.length === 0 ? (
        <p className="muted">No issues detected.</p>
      ) : (
        <ul className="issue-list">
          {diagnosis.issues.map((issue, index) => (
            <li key={`${issue.type}-${index}`} className={`issue ${issue.severity}`}>
              <span className="issue-tag">{issue.severity}</span>
              {issue.message}
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}
