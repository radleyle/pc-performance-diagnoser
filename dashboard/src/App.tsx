import { useEffect, useState } from "react";
import {
  fetchDiagnose,
  fetchHealth,
  fetchMetrics,
  fetchProcesses,
  type DiagnosisResponse,
  type MetricPoint,
  type ProcessRow,
} from "./api";
import AlertsPanel from "./AlertsPanel";
import MetricsChart from "./MetricsChart";
import ProcessTable from "./ProcessTable";
import "./App.css";
import AnalyzePanel from "./AnalyzePanel";

const REFRESH_MS = 5000;

function App() {
  const [apiStatus, setApiStatus] = useState<"loading" | "connected" | "error">(
    "loading"
  );
  const [metrics, setMetrics] = useState<MetricPoint[]>([]);
  const [processes, setProcesses] = useState<ProcessRow[]>([]);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        await fetchHealth();
        const [metricsRes, processesRes, diagnosisRes] = await Promise.all([
          fetchMetrics(60),
          fetchProcesses(),
          fetchDiagnose(),
        ]);

        if (cancelled) return;

        setApiStatus("connected");
        setMetrics(metricsRes.data);
        setProcesses(processesRes.data);
        setDiagnosis(diagnosisRes);
        setErrorMessage("");
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
  }, []);

  return (
    <div className="app">
      <header>
        <h1>PC Performance Diagnoser</h1>
        <p>Live system metrics and AI-powered diagnosis</p>
        {apiStatus === "connected" && (
          <p className="ok">Connected — refreshing every 5s</p>
        )}
        {apiStatus === "error" && (
          <p className="error">
            API error: {errorMessage} (is uvicorn running?)
          </p>
        )}
      </header>

      <main className="grid">
        <MetricsChart data={metrics} />
        <AlertsPanel diagnosis={diagnosis} />
        <AnalyzePanel />
        <ProcessTable processes={processes} />
      </main>
    </div>
  );
}

export default App;