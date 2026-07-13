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
import SlowNowPanel from "./SlowNowPanel";
import LiveProcessPanel from "./LiveProcessPanel";
import StorageBreakdownPanel from "./StorageBreakdownPanel";
import LargeFilesPanel from "./LargeFilesPanel";
import CleanupPanel from "./CleanupPanel";
import StartupPanel from "./StartupPanel";
import SetupBanner from "./SetupBanner";
import OnboardingWizard from "./OnboardingWizard";
import Sidebar, { type AppTab } from "./Sidebar";
import {
  ActionSuggestionsPanel,
  BaselinePanel,
  BootAuditPanel,
  ImpactPanel,
  NetworkPanel,
  WeeklyDigestPanel,
} from "./InsightsPanels";
import {
  DevJunkPanel,
  DuplicatesPanel,
  FolderGrowthPanel,
  SystemHintsPanel,
} from "./StorageExtrasPanels";
import {
  loadAlertLevel,
  requestNotificationPermission,
  saveAlertLevel,
  useStatusNotifications,
  type AlertLevel,
} from "./useNotifications";
import { loadCompactMode, saveCompactMode } from "./useCompactMode";
import { isOnboarded } from "./useOnboarding";
import { useTheme } from "./useTheme";

const REFRESH_MS = 5000;

function App() {
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<AppTab>("overview");
  const [apiStatus, setApiStatus] = useState<"loading" | "connected" | "error">(
    "loading",
  );
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [metrics, setMetrics] = useState<MetricPoint[]>([]);
  const [diagnosis, setDiagnosis] = useState<DiagnosisResponse | null>(null);
  const [summary, setSummary] = useState<ComparisonSummary | null>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [history, setHistory] = useState<DiagnosisHistoryItem[]>([]);
  const [chartMinutes, setChartMinutes] = useState(60);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [alertLevel, setAlertLevel] = useState<AlertLevel>(() => loadAlertLevel());
  const [compactMode, setCompactMode] = useState(() => loadCompactMode());
  const [showOnboarding, setShowOnboarding] = useState(() => !isOnboarded());
  const [retryKey, setRetryKey] = useState(0);

  useStatusNotifications(diagnosis, alertLevel);

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
          error instanceof Error ? error.message : "Unknown error",
        );
      }
    }

    loadData();
    const intervalId = setInterval(loadData, REFRESH_MS);

    return () => {
      cancelled = true;
      clearInterval(intervalId);
    };
  }, [chartMinutes, retryKey]);

  function handleAlertLevelChange(level: AlertLevel) {
    setAlertLevel(level);
    saveAlertLevel(level);
  }

  function handleToggleCompact() {
    setCompactMode((prev) => {
      const next = !prev;
      saveCompactMode(next);
      return next;
    });
  }

  function handleRetryConnection() {
    setApiStatus("loading");
    setRetryKey((value) => value + 1);
  }

  function handleScanComplete() {
    refreshHistory();
    setActiveTab("history");
  }

  const shellClass = compactMode ? "app-shell compact-mode" : "app-shell";

  return (
    <div className={shellClass}>
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        theme={theme}
        onToggleTheme={toggleTheme}
        compactMode={compactMode}
        onToggleCompact={handleToggleCompact}
      />

      <div className="app-main">
        <header className="top-bar">
          <div className="page-heading">
            <h2 className="page-title">
              {activeTab === "overview" && "Overview"}
              {activeTab === "insights" && "Insights"}
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
                  <span>Alerts</span>
                  <select
                    value={alertLevel}
                    onChange={(event) =>
                      handleAlertLevelChange(event.target.value as AlertLevel)
                    }
                  >
                    <option value="all">Warnings + critical</option>
                    <option value="critical">Critical only</option>
                    <option value="off">Off</option>
                  </select>
                </label>
              </div>
            </div>
          )}

          {apiStatus === "error" && (
            <p className="error top-error">API error: {errorMessage}</p>
          )}
        </header>

        <div className="tab-content">
          {showOnboarding && apiStatus === "connected" && (
            <OnboardingWizard onComplete={() => setShowOnboarding(false)} />
          )}

          {apiStatus === "error" && (
            <SetupBanner onRetry={handleRetryConnection} />
          )}

          {apiStatus === "loading" && (
            <p className="muted setup-loading">Connecting to API...</p>
          )}

          {activeTab === "overview" && apiStatus === "connected" && (
            <div className="tab-overview">
              <StatusHero diagnosis={diagnosis} metrics={metrics} />
              <SlowNowPanel />
              <div className="overview-grid">
                <div className="overview-primary">
                  <AlertsPanel diagnosis={diagnosis} />
                  {!compactMode && (
                    <AnalyzePanel onScanComplete={handleScanComplete} />
                  )}
                </div>
                {!compactMode && (
                  <div className="overview-secondary">
                    <DiskPanel metrics={metrics} />
                    <WhatChangedPanel summary={summary} />
                    <ExportPanel />
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === "insights" && apiStatus === "connected" && (
            <div className="insights-tab">
              <WeeklyDigestPanel />
              <ImpactPanel />
              <NetworkPanel />
              <BaselinePanel />
              <BootAuditPanel />
              <ActionSuggestionsPanel />
            </div>
          )}

          {activeTab === "performance" && apiStatus === "connected" && (
            <MetricsChart
              data={metrics}
              minutes={chartMinutes}
              onMinutesChange={setChartMinutes}
            />
          )}

          {activeTab === "storage" && apiStatus === "connected" && (
            <div className="storage-tab">
              <StorageBreakdownPanel />
              <FolderGrowthPanel />
              <LargeFilesPanel />
              <DuplicatesPanel />
              <DevJunkPanel />
              <SystemHintsPanel />
              <CleanupPanel />
              <StartupPanel />
            </div>
          )}

          {activeTab === "processes" && apiStatus === "connected" && (
            <LiveProcessPanel />
          )}

          {activeTab === "history" && apiStatus === "connected" && (
            <DiagnosisHistory history={history} />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
