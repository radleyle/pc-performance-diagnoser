import { useState } from "react";
import { fetchAnalyze, fetchHealth } from "./api";
import { markOnboarded } from "./useOnboarding";
import { requestNotificationPermission } from "./useNotifications";

type Props = {
  onComplete: () => void;
};

export default function OnboardingWizard({ onComplete }: Props) {
  const [step, setStep] = useState(1);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleNext() {
    if (step === 1) {
      try {
        const health = await fetchHealth();
        if (health.api !== "ok") throw new Error("API not ready");
        setMessage("Backend connected.");
        setStep(2);
      } catch {
        setMessage("Start the app with ./scripts/start-desktop.sh first.");
      }
      return;
    }

    if (step === 2) {
      requestNotificationPermission();
      setMessage("Notification permission requested.");
      setStep(3);
      return;
    }

    if (step === 3) {
      setLoading(true);
      try {
        await fetchAnalyze();
        setMessage("First Smart Scan saved to history.");
      } catch {
        setMessage("Smart Scan skipped — Ollama optional. You can run it later.");
      } finally {
        setLoading(false);
        setStep(4);
      }
      return;
    }

    markOnboarded();
    onComplete();
  }

  return (
    <section className="onboarding-wizard">
      <h3>Welcome to Diagnoser</h3>
      <p className="muted">Step {step} of 4</p>
      <ol className="onboarding-steps">
        <li className={step >= 1 ? "active" : ""}>Connect backend</li>
        <li className={step >= 2 ? "active" : ""}>Enable alerts</li>
        <li className={step >= 3 ? "active" : ""}>Run first Smart Scan</li>
        <li className={step >= 4 ? "active" : ""}>Done</li>
      </ol>
      {message && <p className="onboarding-message">{message}</p>}
      <button type="button" className="analyze-btn" disabled={loading} onClick={handleNext}>
        {step === 4 ? "Finish" : loading ? "Scanning..." : "Continue"}
      </button>
    </section>
  );
}
