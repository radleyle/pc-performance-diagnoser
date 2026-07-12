import type { ProcessRow } from "./api";
import PanelShell from "./PanelShell";

type Props = {
  processes: ProcessRow[];
  fullWidth?: boolean;
};

function maxMemory(processes: ProcessRow[]): number {
  if (processes.length === 0) return 1;
  return Math.max(...processes.map((p) => p.memory_mb));
}

export default function ProcessTable({ processes, fullWidth = false }: Props) {
  const peak = maxMemory(processes);

  return (
    <PanelShell
      title="Top apps"
      description="Grouped by application, sorted by memory."
      className={fullWidth ? "panel-full" : ""}
    >
      {processes.length === 0 ? (
        <p className="muted">No process data yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>App</th>
              <th>Procs</th>
              <th>Memory</th>
              <th>CPU</th>
            </tr>
          </thead>
          <tbody>
            {processes.map((proc) => (
              <tr key={proc.app_name}>
                <td>{proc.app_name}</td>
                <td>{proc.process_count}</td>
                <td>
                  <div className="memory-cell">
                    <span>{Math.round(proc.memory_mb)} MB</span>
                    <div className="memory-bar-track">
                      <div
                        className="memory-bar-fill"
                        style={{
                          width: `${Math.min((proc.memory_mb / peak) * 100, 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                </td>
                <td>{proc.cpu_percent.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PanelShell>
  );
}
