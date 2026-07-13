import { useCallback, useEffect, useState } from "react";
import { fetchStorageBreakdown, type FolderSize } from "./api";
import PanelShell from "./PanelShell";

function formatCachedAt(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString();
}

export default function StorageBreakdownPanel() {
  const [folders, setFolders] = useState<FolderSize[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [cacheLabel, setCacheLabel] = useState("");

  const load = useCallback(async (refresh = false) => {
    if (refresh) setRefreshing(true);
    else setLoading(true);

    try {
      const res = await fetchStorageBreakdown(10, refresh);
      setFolders(res.data);
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
  }, []);

  useEffect(() => {
    load(false);
  }, [load]);

  const peak = folders[0]?.size_bytes ?? 1;

  return (
    <PanelShell
      title="Folder breakdown"
      description="Largest folders in your home directory."
      collapsible
      defaultOpen
    >
      <div className="panel-toolbar">
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

      {loading && <p className="muted">Scanning folders...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && folders.length === 0 && (
        <p className="muted">No folders found.</p>
      )}
      {!loading && folders.length > 0 && (
        <ul className="breakdown-list">
          {folders.map((folder) => (
            <li key={folder.path} className="breakdown-item">
              <div className="breakdown-row">
                <span className="breakdown-name">{folder.name}</span>
                <span className="breakdown-size">{folder.size_gb} GB</span>
              </div>
              <div className="memory-bar-track">
                <div
                  className="memory-bar-fill"
                  style={{
                    width: `${Math.max((folder.size_bytes / peak) * 100, 4)}%`,
                  }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}
