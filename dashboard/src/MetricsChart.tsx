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
  diskUsed: number | null;
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

const CHART_COLORS = {
  grid: "var(--chart-grid)",
  axis: "var(--chart-axis)",
  cpu: "#38bdf8",
  ram: "#34d399",
  disk: "#fb923c",
  tooltipBg: "var(--chart-tooltip-bg)",
  tooltipBorder: "var(--border-strong)",
};

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
    diskUsed:
      point.disk_used_percent != null
        ? Math.round(point.disk_used_percent * 10) / 10
        : null,
  }));

  const hasDisk = chartData.some((row) => row.diskUsed != null);

  return (
    <section className="panel chart-panel">
      <div className="panel-header">
        <h2>Performance · {rangeLabel(minutes)}</h2>
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
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={CHART_COLORS.grid}
                vertical={false}
              />
              <XAxis
                dataKey="time"
                minTickGap={30}
                stroke={CHART_COLORS.axis}
                tick={{ fill: "#71717a", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                yAxisId="left"
                domain={[0, 100]}
                unit="%"
                stroke={CHART_COLORS.axis}
                tick={{ fill: "#71717a", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                unit=" MB"
                stroke={CHART_COLORS.axis}
                tick={{ fill: "#71717a", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: CHART_COLORS.tooltipBg,
                  border: `1px solid ${CHART_COLORS.tooltipBorder}`,
                  borderRadius: 12,
                  fontSize: 12,
                }}
                labelStyle={{ color: "#a1a1aa" }}
              />
              <Legend
                wrapperStyle={{ fontSize: 12, color: "#a1a1aa", paddingTop: 8 }}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="cpu"
                name="CPU %"
                stroke={CHART_COLORS.cpu}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="ramAvailable"
                name="RAM available"
                stroke={CHART_COLORS.ram}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 0 }}
              />
              {hasDisk && (
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="diskUsed"
                  name="Disk used %"
                  stroke={CHART_COLORS.disk}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                  activeDot={{ r: 4, strokeWidth: 0 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
