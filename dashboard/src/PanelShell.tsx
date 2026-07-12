import { useState, type ReactNode } from "react";

type Props = {
  title: string;
  description?: string;
  collapsible?: boolean;
  defaultOpen?: boolean;
  className?: string;
  children: ReactNode;
};

export default function PanelShell({
  title,
  description,
  collapsible = false,
  defaultOpen = true,
  className = "",
  children,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);

  if (!collapsible) {
    return (
      <section className={`panel ${className}`.trim()}>
        <h2>{title}</h2>
        {description && <p className="panel-desc">{description}</p>}
        {children}
      </section>
    );
  }

  return (
    <section
      className={`panel collapsible-panel ${open ? "is-open" : "is-collapsed"} ${className}`.trim()}
    >
      <button
        type="button"
        className="collapsible-trigger"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <div className="collapsible-trigger-text">
          <h2>{title}</h2>
          {description && <p className="panel-desc">{description}</p>}
        </div>
        <span className="collapsible-chevron" aria-hidden="true" />
      </button>
      {open && <div className="collapsible-body">{children}</div>}
    </section>
  );
}
