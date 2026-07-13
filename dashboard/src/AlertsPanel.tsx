import { useState } from "react";
import type { DiagnosisResponse, Issue } from "./api";
import { explainIssue } from "./api";
import PanelShell from "./PanelShell";

type Props = {
  diagnosis: DiagnosisResponse | null;
};

export default function AlertsPanel({ diagnosis }: Props) {
  const [explaining, setExplaining] = useState<string | null>(null);
  const [explanations, setExplanations] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

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

  async function handleExplain(issue: Issue, index: number) {
    const key = `${issue.type}-${index}`;
    setExplaining(key);
    setError("");
    try {
      const res = await explainIssue(issue);
      setExplanations((prev) => ({ ...prev, [key]: res.explanation }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Explain failed");
    } finally {
      setExplaining(null);
    }
  }

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
          {diagnosis.issues.map((issue, index) => {
            const key = `${issue.type}-${index}`;
            return (
              <li key={key} className={`issue ${issue.severity}`}>
                <span className="issue-tag">{issue.severity}</span>
                {issue.message}
                <button
                  type="button"
                  className="ghost-btn issue-explain-btn"
                  disabled={explaining === key}
                  onClick={() => handleExplain(issue, index)}
                >
                  {explaining === key ? "..." : "Explain"}
                </button>
                {explanations[key] && (
                  <p className="issue-explanation muted">{explanations[key]}</p>
                )}
              </li>
            );
          })}
        </ul>
      )}
      {error && <p className="error">{error}</p>}
    </PanelShell>
  );
}
