import { useState } from "react";
import { fetchAnalyze, type AnalyzeResponse } from "./api";

export default function AnalyzePanel() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState("");

  async function handleAnalyze() {
    setLoading(true);
    setError("");

    try {
      const data = await fetchAnalyze();
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Analyze failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <h2>AI analysis</h2>
      <p className="muted">
        Runs detection, then asks the local LLM to explain the results.
      </p>

      <button onClick={handleAnalyze} disabled={loading} className="analyze-btn">
        {loading ? "Analyzing..." : "Analyze now"}
      </button>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="analysis-result">
          <p>
            Status: <span className={`badge ${result.status}`}>{result.status}</span>
          </p>
          <p>{result.explanation}</p>
        </div>
      )}
    </section>
  );
}