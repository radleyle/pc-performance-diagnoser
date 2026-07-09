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
  };
  
  function formatTime(timestamp: number): string {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }
  
  export default function MetricsChart({ data }: Props) {
    const chartData: ChartRow[] = data.map((point) => ({
      time: formatTime(point.timestamp),
      cpu: point.cpu_percent,
      ramAvailable: Math.round(point.ram_available_mb),
    }));
  
    if (chartData.length === 0) {
      return (
        <section className="panel">
          <h2>CPU & RAM (last hour)</h2>
          <p className="muted">No metrics yet — start the collector.</p>
        </section>
      );
    }
  
    return (
      <section className="panel">
        <h2>CPU & RAM (last hour)</h2>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" minTickGap={30} />
              <YAxis yAxisId="left" domain={[0, 100]} unit="%" />
              <YAxis yAxisId="right" orientation="right" unit=" MB" />
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
      </section>
    );
  }