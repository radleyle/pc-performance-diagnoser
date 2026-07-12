import { useEffect, useState } from "react";
import {
  fetchDiagnose,
  fetchDiagnosisHistory,
  fetchHealth,
  fetchMetrics,
  fetchProcesses,
  type DiagnosisHistoryItem,
  type DiagnosisResponse,
  type HealthResponse,
  type MetricPoint,
  type ProcessRow,
} from "./api";
import AlertsPanel from "./AlertsPanel";
import MetricsChart from "./MetricsChart";
import ProcessTable from "./ProcessTable";
import "./App.css";
import AnalyzePanel from "./AnalyzePanel";
import ServiceStatus from "./ServiceStatus";
import DiagnosisHistory from "./DiagnosisHistory";
import DiskPanel from "./DiskPanel";

const REFRESH_MS = 5000;

function App() {
  const [apiStatus, setApiStatus] = useState<"loading" | "connected" | "error">(
    "loading"
  );
  const [health, setHealth] = useState<HealthResponse | null>(null);  
  const [metrics, setMetrics] = useState<MetricPoint[]>([]);
  const [processes, setProcesses] = useState<ProcessRow[]>([]);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [history, setHistory] = useState<DiagnosisHistoryItem[]>([]);
  const [chartMinutes, setChartMinutes] = useState(60);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        const healthRes = await fetchHealth();
        const [metricsRes, processesRes, diagnosisRes, historyRes] = await Promise.all([
          fetchMetrics(chartMinutes),
          fetchProcesses(),
          fetchDiagnose(),
          fetchDiagnosisHistory(10),
        ]);

        if (cancelled) return;

        setApiStatus("connected");
        setHealth(healthRes);
        setMetrics(metricsRes.data);
        setProcesses(processesRes.data);
        setDiagnosis(diagnosisRes);
        setErrorMessage("");
        setHistory(historyRes.data);
        setLastUpdated(new Date());
      } catch (error) {
        if (cancelled) return;
        setApiStatus("error");
        setErrorMessage(
          error instanceof Error ? error.message : "Unknown error"
        );
      }
    }

    loadData();
    const intervalId = setInterval(loadData, REFRESH_MS);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [chartMinutes]);

  return (
    <div className="app">
      <header>
        <h1>PC Performance Diagnoser</h1>
        <p className="subtitle">Live system metrics and AI-powered diagnosis</p>
        {apiStatus === "connected" && (
          <>
            <ServiceStatus health={health} />
            <p className="ok">
              Refreshing every 5s
              {lastUpdated && (
                <span className="last-updated">
                  {" "}· Last updated {lastUpdated.toLocaleTimeString()}
                </span>
              )}
            </p>
          </>
        )}
        {apiStatus === "error" && (
          <p className="error">
            API error: {errorMessage} (is uvicorn running?)
          </p>
        )}
      </header>

      <main className="grid">
        <div className="main-column">
          <MetricsChart
            data={metrics}
            minutes={chartMinutes}
            onMinutesChange={setChartMinutes}
          />
        </div>

        <div className="side-column">
          <DiskPanel metrics={metrics} />
          <AlertsPanel diagnosis={diagnosis} />
          <AnalyzePanel />
          <ProcessTable processes={processes} />
        </div>

        <DiagnosisHistory history={history} />
      </main>
    </div>
  );
}

export default App;