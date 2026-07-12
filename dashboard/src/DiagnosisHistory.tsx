import type { DiagnosisHistoryItem } from "./api";
import PanelShell from "./PanelShell";

type Props = {
  history: DiagnosisHistoryItem[];
};

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function DiagnosisHistory({ history }: Props) {
  return (
    <PanelShell
      title="Scan history"
      description="Past AI analyses from Smart Scan."
      className="history-panel panel-full"
    >
      {history.length === 0 ? (
        <p className="muted">
          No scans yet — run <strong>Smart Scan</strong> on the Overview tab.
        </p>
      ) : (
        <ul className="history-list">
          {history.map((item) => (
            <li key={item.id} className="history-item">
              <div className="history-header">
                <span className="history-time">{formatTime(item.timestamp)}</span>
                <span className={`badge ${item.status}`}>{item.status}</span>
                {item.issue_count > 0 && (
                  <span className="history-issues">
                    {item.issue_count} issue{item.issue_count !== 1 ? "s" : ""}
                  </span>
                )}
              </div>
              {item.explanation && (
                <p className="history-explanation">{item.explanation}</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}
