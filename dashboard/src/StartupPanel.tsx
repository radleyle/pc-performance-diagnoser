import { useEffect, useState } from "react";
import { fetchStartupItems, type StartupItem } from "./api";
import PanelShell from "./PanelShell";

export default function StartupPanel() {
  const [items, setItems] = useState<StartupItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await fetchStartupItems();
        if (!cancelled) {
          setItems(res.data);
          setError("");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load");
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
      title="Startup items"
      description="Launch agents that run at login (read-only)."
      collapsible
      defaultOpen={false}
    >
      {loading && <p className="muted">Loading startup items...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="muted">No startup items found (macOS only).</p>
      )}
      {!loading && items.length > 0 && (
        <ul className="startup-list">
          {items.map((item) => (
            <li key={item.path} className="startup-item">
              <strong>{item.name}</strong>
              <span className="muted">{item.location}</span>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}
