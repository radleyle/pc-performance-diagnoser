import { useEffect, useState } from "react";
import { fetchLargeFiles, type LargeFile } from "./api";
import PanelShell from "./PanelShell";

export default function LargeFilesPanel() {
  const [files, setFiles] = useState<LargeFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const res = await fetchLargeFiles();
        if (!cancelled) {
          setFiles(res.data);
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

  return (
    <PanelShell
      title="Large files"
      description="Files over 500 MB in your home folder."
      collapsible
      defaultOpen
    >
      {loading && <p className="muted">Searching for large files...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && files.length === 0 && (
        <p className="muted">No large files found.</p>
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
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}
