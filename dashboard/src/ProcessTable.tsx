import type { ProcessRow } from "./api";

type Props = {
  processes: ProcessRow[];
};

export default function ProcessTable({ processes }: Props) {
  return (
    <section className="panel">
      <h2>Top apps by memory</h2>
      {processes.length === 0 ? (
        <p className="muted">No process data yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>App</th>
              <th>Processes</th>
              <th>Memory (MB)</th>
              <th>CPU %</th>
            </tr>
          </thead>
          <tbody>
            {processes.map((proc) => (
              <tr key={proc.app_name}>
                <td>{proc.app_name}</td>
                <td>{proc.process_count}</td>
                <td>{Math.round(proc.memory_mb)}</td>
                <td>{proc.cpu_percent.toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}