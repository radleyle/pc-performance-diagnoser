import { useEffect, useState } from "react";
import { fetchStartupItems, toggleStartupItem, type StartupItem } from "./api";
import PanelShell from "./PanelShell";

export default function StartupPanel() {
  const [items, setItems] = useState<StartupItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyPath, setBusyPath] = useState<string | null>(null);

  async function load() {
    try {
      const res = await fetchStartupItems();
      setItems(res.data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleToggle(item: StartupItem) {
    setBusyPath(item.path);
    try {
      await toggleStartupItem(item.path, !item.enabled);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Toggle failed");
    } finally {
      setBusyPath(null);
    }
  }

  return (
    <PanelShell
      title="Startup items"
      description="Launch agents at login — disable with care."
      collapsible
      defaultOpen={false}
    >
      {loading && <p className="muted">Loading startup items...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && items.length === 0 && (
        <p className="muted">No startup items found (macOS only).</p>
      )}
      {!loading && items.length > 0 && (
        <ul className="startup-list">
          {items.map((item) => (
            <li key={item.path} className="startup-item">
              <div className="file-row">
                <strong>{item.name}</strong>
                <button
                  type="button"
                  className="ghost-btn"
                  disabled={busyPath === item.path}
                  onClick={() => handleToggle(item)}
                >
                  {busyPath === item.path
                    ? "..."
                    : item.enabled
                      ? "Disable"
                      : "Enable"}
                </button>
              </div>
              <span className="muted">{item.location}</span>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}
