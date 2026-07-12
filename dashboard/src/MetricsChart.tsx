import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MetricPoint } from "./api";

type ChartRow = {
  time: string;
  cpu: number;
  ramAvailable: number;
};

type Props = {
  data: MetricPoint[];
  minutes: number;
  onMinutesChange: (minutes: number) => void;
};

const TIME_RANGES = [
  { label: "15m", minutes: 15 },
  { label: "1h", minutes: 60 },
  { label: "6h", minutes: 360 },
] as const;

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function rangeLabel(minutes: number): string {
  if (minutes < 60) return `${minutes} minutes`;
  if (minutes < 1440) return `${minutes / 60} hours`;
  return `${minutes / 1440} days`;
}

export default function MetricsChart({ data, minutes, onMinutesChange }: Props) {
  const chartData: ChartRow[] = data.map((point) => ({
    time: formatTime(point.timestamp),
    cpu: point.cpu_percent,
    ramAvailable: Math.round(point.ram_available_mb),
  }));

  return (
    <section className="panel chart-panel">
      <div className="panel-header">
        <h2>CPU & RAM ({rangeLabel(minutes)})</h2>
        <div className="time-range">
          {TIME_RANGES.map((range) => (
            <button
              key={range.minutes}
              type="button"
              className={`range-btn ${minutes === range.minutes ? "active" : ""}`}
              onClick={() => onMinutesChange(range.minutes)}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {chartData.length === 0 ? (
        <p className="muted">No metrics yet — start the collector.</p>
      ) : (
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="time" minTickGap={30} stroke="#888" />
              <YAxis yAxisId="left" domain={[0, 100]} unit="%" stroke="#888" />
              <YAxis yAxisId="right" orientation="right" unit=" MB" stroke="#888" />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="cpu"
                name="CPU %"
                stroke="#3b82f6"
                dot={false}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="ramAvailable"
                name="RAM available"
                stroke="#22c55e"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
