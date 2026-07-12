import { useState } from "react";
import { fetchAnalyze, type AnalyzeResponse } from "./api";
import PanelShell from "./PanelShell";
import ScanRing from "./ScanRing";

type Props = {
  onScanComplete?: () => void;
};

export default function AnalyzePanel({ onScanComplete }: Props) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState("");

  async function handleAnalyze() {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await fetchAnalyze();
      setResult(data);
      onScanComplete?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analyze failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <PanelShell
      title="Smart Scan"
      description="Run detection and get a plain-English explanation from your local AI."
    >
      {loading ? (
        <ScanRing label="Analyzing metrics with local AI..." />
      ) : (
        <button onClick={handleAnalyze} disabled={loading} className="analyze-btn">
          Run smart scan
        </button>
      )}

      {error && <p className="error">{error}</p>}

      {result && !loading && (
        <div className="analysis-result">
          <p>
            <span className={`badge ${result.status}`}>{result.status}</span>
          </p>
          <p>{result.explanation}</p>
        </div>
      )}
    </PanelShell>
  );
}
