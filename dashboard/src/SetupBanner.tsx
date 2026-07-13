type Props = {
  onRetry: () => void;
};

export default function SetupBanner({ onRetry }: Props) {
  return (
    <section className="setup-banner" role="alert">
      <div className="setup-banner-copy">
        <h3>Backend not connected</h3>
        <p>
          The desktop app needs the Python collector and API. First time? Run
          install once, then launch.
        </p>
        <ol className="setup-steps">
          <li>
            <code>./scripts/install.sh</code>
          </li>
          <li>
            <code>./scripts/start-desktop.sh</code> — or double-click{" "}
            <code>scripts/Launch Diagnoser.command</code>
          </li>
        </ol>
        <p className="muted setup-note">
          After the first successful launch, the app remembers your project
          folder and can auto-start the backend next time.
        </p>
      </div>
      <button type="button" className="analyze-btn" onClick={onRetry}>
        Retry connection
      </button>
    </section>
  );
}
