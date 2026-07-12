import { useCallback, useEffect, useState } from "react";
import {
  fetchDiagnose,
  fetchDiagnosisHistory,
  fetchHealth,
  fetchMetrics,
  fetchSummary,
  type ComparisonSummary,
  type DiagnosisHistoryItem,
  type DiagnosisResponse,
  type HealthResponse,
  type MetricPoint,
} from "./api";
import AlertsPanel from "./AlertsPanel";
import MetricsChart from "./MetricsChart";
import "./App.css";
import AnalyzePanel from "./AnalyzePanel";
import ServiceStatus from "./ServiceStatus";
import DiagnosisHistory from "./DiagnosisHistory";
import DiskPanel from "./DiskPanel";
import WhatChangedPanel from "./WhatChangedPanel";
import ExportPanel from "./ExportPanel";
import StatusHero from "./StatusHero";
import LiveProcessPanel from "./LiveProcessPanel";
import StorageBreakdownPanel from "./StorageBreakdownPanel";
import LargeFilesPanel from "./LargeFilesPanel";
import CleanupPanel from "./CleanupPanel";
import StartupPanel from "./StartupPanel";
import Sidebar, { type AppTab } from "./Sidebar";
import {
  requestNotificationPermission,
  useCriticalNotifications,
} from "./useNotifications";
import { useTheme } from "./useTheme";

const REFRESH_MS = 5000;

function App() {
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<AppTab>("overview");
  const [apiStatus, setApiStatus] = useState<"loading" | "connected" | "error">(
    "loading"
  );
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricPoint[]>([]);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResponse | null>(null);
  const [summary, setSummary] = useState<ComparisonSummary | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [history, setHistory] = useState<DiagnosisHistoryItem[]>([]);
  const [chartMinutes, setChartMinutes] = useState(60);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);

  useCriticalNotifications(diagnosis, notificationsEnabled);

  const refreshHistory = useCallback(async () => {
    const historyRes = await fetchDiagnosisHistory(10);
    setHistory(historyRes.data);
  }, []);

  useEffect(() => {
    requestNotificationPermission();
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      try {
        const healthRes = await fetchHealth();
        const [metricsRes, diagnosisRes, historyRes, summaryRes] =
          await Promise.all([
            fetchMetrics(chartMinutes),
            fetchDiagnose(),
            fetchDiagnosisHistory(10),
            fetchSummary(60),
          ]);

        if (cancelled) return;

        setApiStatus("connected");
        setHealth(healthRes);
        setMetrics(metricsRes.data);
        setDiagnosis(diagnosisRes);
        setSummary(summaryRes);
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

  function handleScanComplete() {
    refreshHistory();
    setActiveTab("history");
  }

  return (
    <div className="app-shell">
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <div className="app-main">
        <header className="top-bar">
          <div className="page-heading">
            <h2 className="page-title">
              {activeTab === "overview" && "Overview"}
              {activeTab === "performance" && "Performance"}
              {activeTab === "storage" && "Storage"}
              {activeTab === "processes" && "Processes"}
              {activeTab === "history" && "History"}
            </h2>
            <p className="page-subtitle">
              Real-time system monitoring and diagnosis
            </p>
          </div>

          {apiStatus === "connected" && (
            <div className="top-bar-meta">
              <ServiceStatus health={health} />
              <div className="top-bar-actions">
                <span className="live-pill">
                  <span className="live-dot" />
                  Live · 5s
                  {lastUpdated && (
                    <span className="last-updated">
                      · {lastUpdated.toLocaleTimeString()}
                    </span>
                  )}
                </span>
                <label className="notification-toggle">
                  <input
                    type="checkbox"
                    checked={notificationsEnabled}
                    onChange={(event) =>
                      setNotificationsEnabled(event.target.checked)
                    }
                  />
                  Alerts
                </label>
              </div>
            </div>
          )}

          {apiStatus === "error" && (
            <p className="error top-error">API error: {errorMessage}</p>
          )}
        </header>

        <div className="tab-content">
          {activeTab === "overview" && (
            <div className="tab-overview">
              {apiStatus === "connected" && (
                <StatusHero diagnosis={diagnosis} metrics={metrics} />
              )}
              <div className="overview-grid">
                <div className="overview-primary">
                  <AlertsPanel diagnosis={diagnosis} />
                  <AnalyzePanel onScanComplete={handleScanComplete} />
                </div>
                <div className="overview-secondary">
                  <DiskPanel metrics={metrics} />
                  <WhatChangedPanel summary={summary} />
                  <ExportPanel />
                </div>
              </div>
            </div>
          )}

          {activeTab === "performance" && (
            <MetricsChart
              data={metrics}
              minutes={chartMinutes}
              onMinutesChange={setChartMinutes}
            />
          )}

          {activeTab === "storage" && (
            <div className="storage-tab">
              <StorageBreakdownPanel />
              <LargeFilesPanel />
              <CleanupPanel />
              <StartupPanel />
            </div>
          )}

          {activeTab === "processes" && <LiveProcessPanel />}

          {activeTab === "history" && <DiagnosisHistory history={history} />}
        </div>
      </div>
    </div>
  );
}

export default App;
