import { useEffect, useState } from "react";
import { fetchStorageBreakdown, type FolderSize } from "./api";
import PanelShell from "./PanelShell";

export default function StorageBreakdownPanel() {
  const [folders, setFolders] = useState<FolderSize[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const res = await fetchStorageBreakdown();
        if (!cancelled) {
          setFolders(res.data);
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Scan failed");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const peak = folders[0]?.size_bytes ?? 1;

  return (
    <PanelShell
      title="Folder breakdown"
      description="Largest folders in your home directory."
      collapsible
      defaultOpen
    >
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
