import type { ProcessRow } from "./api";

type Props = {
  processes: ProcessRow[];
};

export default function ProcessTable({ processes }: Props) {
  return (
    <section className="panel">
      <h2>Top processes by memory</h2>
      {processes.length === 0 ? (
        <p className="muted">No process data yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Process</th>
              <th>Memory (MB)</th>
              <th>CPU %</th>
            </tr>
          </thead>
          <tbody>
            {processes.map((proc, index) => (
              <tr key={`${proc.process_name}-${index}`}>
                <td>{proc.process_name}</td>
                <td>{Math.round(proc.memory_mb)}</td>
                <td>{proc.cpu_percent ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}