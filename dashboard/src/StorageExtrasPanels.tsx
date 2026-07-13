import { useEffect, useState } from "react";
import {
  fetchFolderGrowth,
  fetchDuplicates,
  fetchDevJunk,
  fetchSystemHints,
  revealInFinder,
  type DuplicateGroup,
  type DevJunkItem,
  type FolderGrowthItem,
  type SystemHint,
} from "./api";
import PanelShell from "./PanelShell";

export function FolderGrowthPanel() {
  const [rows, setRows] = useState<FolderGrowthItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchFolderGrowth(7)
      .then((res) => setRows(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PanelShell title="Folder growth" description="What grew in the last 7 days." collapsible>
      {loading && <p className="muted">Comparing folder history...</p>}
      {!loading && rows.length === 0 && <p className="muted">No history yet.</p>}
      <ul className="growth-list">
        {rows.map((row) => (
          <li key={row.path}>
            <strong>{row.name}</strong> — {row.size_gb} GB
            {row.has_history && (
              <span className={row.delta_gb >= 0 ? "delta-up" : "delta-down"}>
                {" "}
                ({row.delta_gb >= 0 ? "+" : ""}
                {row.delta_gb} GB)
              </span>
            )}
          </li>
        ))}
      </ul>
    </PanelShell>
  );
}

export function DuplicatesPanel() {
  const [groups, setGroups] = useState<DuplicateGroup[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDuplicates(10)
      .then((res) => setGroups(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PanelShell title="Duplicates" description="Same name + size file groups." collapsible defaultOpen={false}>
      {loading && <p className="muted">Scanning...</p>}
      <ul className="duplicate-list">
        {groups.map((group) => (
          <li key={`${group.name}-${group.size_mb}`}>
            <strong>{group.name}</strong> — {group.count} copies · waste {group.waste_mb} MB
          </li>
        ))}
      </ul>
    </PanelShell>
  );
}

export function DevJunkPanel() {
  const [items, setItems] = useState<DevJunkItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDevJunk()
      .then((res) => setItems(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PanelShell title="Developer junk" description="Build artifacts and dev caches to review." collapsible defaultOpen={false}>
      {loading && <p className="muted">Scanning...</p>}
      <ul className="dev-junk-list">
        {items.map((item) => (
          <li key={item.path}>
            <div className="file-row">
              <strong>{item.name}</strong>
              <span>{item.size_mb} MB</span>
            </div>
            <p className="file-path muted">{item.path}</p>
            <button type="button" className="ghost-btn file-reveal-btn" onClick={() => revealInFinder(item.path)}>
              Show in Finder
            </button>
          </li>
        ))}
      </ul>
    </PanelShell>
  );
}

export function SystemHintsPanel() {
  const [hints, setHints] = useState<SystemHint[]>([]);

  useEffect(() => {
    fetchSystemHints().then((res) => setHints(res.data));
  }, []);

  return (
    <PanelShell title="System storage hints" description="Photos, iCloud, backups, snapshots." collapsible defaultOpen={false}>
      {hints.length === 0 ? (
        <p className="muted">No hints found.</p>
      ) : (
        <ul className="hints-list">
          {hints.map((hint) => (
            <li key={hint.name}>
              <strong>{hint.name}</strong>
              {hint.size_gb != null && <span> — {hint.size_gb} GB</span>}
              <p className="muted">{hint.hint}</p>
            </li>
          ))}
        </ul>
      )}
    </PanelShell>
  );
}
