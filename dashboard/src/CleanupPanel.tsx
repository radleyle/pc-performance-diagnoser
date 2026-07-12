import { useEffect, useState } from "react";
import {
  fetchCleanupPreview,
  runCleanup,
  type CleanupAction,
  type CleanupPreview,
} from "./api";
import PanelShell from "./PanelShell";

export default function CleanupPanel() {
  const [preview, setPreview] = useState<CleanupPreview | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadPreview() {
    setLoading(true);
    try {
      const data = await fetchCleanupPreview();
      setPreview(data);
      setSelected(
        new Set(data.actions.filter((a) => a.available).map((a) => a.id)),
      );
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load preview");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadPreview();
  }, []);

  function toggleAction(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleCleanup() {
    if (selected.size === 0) return;
    setRunning(true);
    setMessage("");
    setError("");

    try {
      const result = await runCleanup([...selected]);
      const msgs = result.results.map((r) => r.message).join(" · ");
      setMessage(msgs);
      await loadPreview();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Cleanup failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <PanelShell
      title="Safe cleanup"
      description="Review and reclaim space from Trash and user caches."
    >
      {loading && <p className="muted">Calculating reclaimable space...</p>}
      {error && <p className="error">{error}</p>}
      {preview && !loading && (
        <>
          <p className="cleanup-total">
            Up to <strong>{preview.total_reclaimable_mb} MB</strong> reclaimable
          </p>
          <ul className="cleanup-list">
            {preview.actions.map((action: CleanupAction) => (
              <li key={action.id} className="cleanup-item">
                <label className="cleanup-label">
                  <input
                    type="checkbox"
                    checked={selected.has(action.id)}
                    disabled={!action.available || running}
                    onChange={() => toggleAction(action.id)}
                  />
                  <span>
                    <strong>{action.label}</strong> — {action.size_mb} MB
                    <span className="muted desc-line">{action.description}</span>
                  </span>
                </label>
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="analyze-btn"
            disabled={running || selected.size === 0}
            onClick={handleCleanup}
          >
            {running ? "Cleaning..." : "Run cleanup"}
          </button>
          {message && <p className="ok">{message}</p>}
        </>
      )}
    </PanelShell>
  );
}
