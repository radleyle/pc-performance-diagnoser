type Props = {
  label?: string;
};

export default function ScanRing({ label = "Scanning system..." }: Props) {
  return (
    <div className="scan-ring-wrap" role="status" aria-live="polite">
      <div className="scan-ring" aria-hidden="true">
        <div className="scan-ring-track" />
        <div className="scan-ring-spinner" />
        <div className="scan-ring-core">
          <span>AI</span>
        </div>
      </div>
      <p className="scan-ring-label">{label}</p>
    </div>
  );
}
