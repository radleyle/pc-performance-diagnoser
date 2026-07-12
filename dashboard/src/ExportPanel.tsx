import { useState } from "react";
import { fetchReport } from "./api";

export default function ExportPanel() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleExport() {
    setLoading(true);
    setError("");

    try {
      const report = await fetchReport();
      const blob = new Blob([JSON.stringify(report, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      const link = document.createElement("a");
      link.href = url;
      link.download = `pc-diagnoser-report-${stamp}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <h2>Export report</h2>
      <p className="muted">
        Download a JSON snapshot of diagnosis, comparison, and top processes.
      </p>
      <button
        type="button"
        onClick={handleExport}
        disabled={loading}
        className="analyze-btn secondary-btn"
      >
        {loading ? "Exporting..." : "Download report"}
      </button>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
