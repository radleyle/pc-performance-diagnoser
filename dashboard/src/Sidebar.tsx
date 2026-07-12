import AppIcon from "./AppIcon";

export type AppTab =
  | "overview"
  | "performance"
  | "storage"
  | "processes"
  | "history";

type NavItem = {
  id: AppTab;
  label: string;
};

const NAV_ITEMS: NavItem[] = [
  { id: "overview", label: "Overview" },
  { id: "performance", label: "Performance" },
  { id: "storage", label: "Storage" },
  { id: "processes", label: "Processes" },
  { id: "history", label: "History" },
];

type Props = {
  activeTab: AppTab;
  onTabChange: (tab: AppTab) => void;
  theme: "dark" | "light";
  onToggleTheme: () => void;
};

function NavIcon({ tab }: { tab: AppTab }) {
  switch (tab) {
    case "overview":
      return (
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <circle cx="10" cy="10" r="7" fill="none" stroke="currentColor" strokeWidth="1.6" />
          <circle cx="10" cy="10" r="2.5" fill="currentColor" />
        </svg>
      );
    case "performance":
      return (
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <path
            d="M2 14 L6 9 L10 11 L14 5 L18 8"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "storage":
      return (
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <ellipse cx="10" cy="13" rx="7" ry="3" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M3 13 V9 C3 7 6.5 5 10 5 S17 7 17 9 V13" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </svg>
      );
    case "processes":
      return (
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <rect x="3" y="4" width="14" height="3" rx="1" fill="currentColor" opacity="0.9" />
          <rect x="3" y="9" width="10" height="3" rx="1" fill="currentColor" opacity="0.7" />
          <rect x="3" y="14" width="12" height="3" rx="1" fill="currentColor" opacity="0.5" />
        </svg>
      );
    case "history":
      return (
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <path
            d="M10 4a6 6 0 1 1 0 12A6 6 0 0 1 10 4zm0 3v3.2l2.4 1.4"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
        </svg>
      );
  }
}

export default function Sidebar({
  activeTab,
  onTabChange,
  theme,
  onToggleTheme,
}: Props) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark">
          <AppIcon size={36} />
        </div>
        <div>
          <h1>Diagnoser</h1>
          <p className="subtitle">Performance Monitor</p>
        </div>
      </div>

      <nav className="sidebar-nav" aria-label="Main navigation">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`nav-item ${activeTab === item.id ? "active" : ""}`}
            onClick={() => onTabChange(item.id)}
            aria-current={activeTab === item.id ? "page" : undefined}
          >
            <span className="nav-icon">
              <NavIcon tab={item.id} />
            </span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button
          type="button"
          className="theme-toggle"
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
        >
          <span className="theme-toggle-icon" aria-hidden="true">
            {theme === "dark" ? "☀" : "☾"}
          </span>
          <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>
        </button>
      </div>
    </aside>
  );
}
