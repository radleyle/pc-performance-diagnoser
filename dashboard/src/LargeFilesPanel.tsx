import { useCallback, useEffect, useState } from "react";
import { fetchLargeFiles, revealInFinder, type LargeFile } from "./api";
import PanelShell from "./PanelShell";

function formatCachedAt(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString();
}

export default function LargeFilesPanel() {
  const [files, setFiles] = useState<LargeFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [cacheLabel, setCacheLabel] = useState("");
  const [minMb, setMinMb] = useState(500);
  const [revealingPath, setRevealingPath] = useState<string | null>(null);

  const load = useCallback(
    async (refresh = false) => {
      if (refresh) setRefreshing(true);
      else setLoading(true);

      try {
        const res = await fetchLargeFiles(minMb, 15, refresh);
        setFiles(res.data);
        setError("");

        if (res.from_cache) {
          const stale = res.stale ? " · rescan recommended" : "";
          setCacheLabel(`Cached ${formatCachedAt(res.cached_at)}${stale}`);
        } else {
          setCacheLabel(`Scanned ${formatCachedAt(res.cached_at)}`);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Scan failed");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [minMb],
  );

  useEffect(() => {
    load(false);
  }, [load]);

  async function handleReveal(path: string) {
    setRevealingPath(path);
    try {
      await revealInFinder(path);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reveal file");
    } finally {
      setRevealingPath(null);
    }
  }

  return (
    <PanelShell
      title="Large files"
      description="Review large files before deleting them elsewhere."
      collapsible
      defaultOpen
    >
      <div className="panel-toolbar">
        <label className="min-size-control">
          Min size
          <select
            value={minMb}
            onChange={(event) => setMinMb(Number(event.target.value))}
            disabled={loading || refreshing}
          >
            <option value={250}>250 MB</option>
            <option value={500}>500 MB</option>
            <option value={1000}>1 GB</option>
            <option value={2000}>2 GB</option>
          </select>
        </label>
        {cacheLabel && <span className="cache-meta muted">{cacheLabel}</span>}
        <button
          type="button"
          className="ghost-btn"
          disabled={loading || refreshing}
          onClick={() => load(true)}
        >
          {refreshing ? "Rescanning..." : "Rescan"}
        </button>
      </div>

      {loading && <p className="muted">Searching for large files...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && files.length === 0 && (
        <p className="muted">No large files found at this threshold.</p>
      )}
      {!loading && files.length > 0 && (
        <ul className="file-list">
          {files.map((file) => (
            <li key={file.path} className="file-item">
              <div className="file-row">
                <strong>{file.name}</strong>
                <span>{file.size_mb} MB</span>
              </div>
              <p className="file-path muted">{file.path}</p>
              <button
                type="button"
                className="ghost-btn file-reveal-btn"
                disabled={revealingPath === file.path}
                onClick={() => handleReveal(file.path)}
              >
                {revealingPath === file.path ? "Opening..." : "Show in Finder"}
              </button>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}
