import { useEffect, useRef, useState } from "react";
import "../styles/LoadingOverlay.css";

const STEPS = [
  { emoji: "📄", label: "Extracting report content..." },
  { emoji: "🧠", label: "AI analyzing your report..." },
  { emoji: "⚠️", label: "Identifying abnormal values..." },
  { emoji: "✍️", label: "Writing plain-language explanation..." },
  { emoji: "🌐", label: "Applying language preferences..." },
];

const STEP_INTERVAL = 1800;
const TICK = 200;
const TOTAL_DURATION = STEP_INTERVAL * STEPS.length;

export default function LoadingOverlay({ visible }) {
  const [activeStep, setActiveStep] = useState(0);
  const [progress, setProgress] = useState(0);

  const stepTimerRef = useRef(null);
  const progressTimerRef = useRef(null);

  useEffect(() => {
    if (!visible) return;

    // Reset
    setActiveStep(0);
    setProgress(0);

    stepTimerRef.current = setInterval(() => {
      setActiveStep((prev) =>
        prev < STEPS.length - 1 ? prev + 1 : prev
      );
    }, STEP_INTERVAL);

    const increment = (TICK / TOTAL_DURATION) * 92;
    progressTimerRef.current = setInterval(() => {
      setProgress((prev) => {
        const next = prev + increment;
        return next >= 92 ? 92 : next;
      });
    }, TICK);

    return () => {
      clearInterval(stepTimerRef.current);
      clearInterval(progressTimerRef.current);
    };
  }, [visible]);

  if (!visible) return null;

  return (
    <div className="lo-backdrop">
      <div className="lo-card">
        <div className="lo-icon">🔬</div>

        <h2 className="lo-title">Analyzing Your Report</h2>
        <p className="lo-subtitle">Our AI is carefully reading your medical report…</p>

        <ul className="lo-steps">
          {STEPS.map((step, i) => (
            <li
              key={i}
              className={`lo-step ${i <= activeStep ? "lo-step--active" : ""} ${
                i < activeStep ? "lo-step--done" : ""
              }`}
            >
              <span className="lo-step-emoji">{step.emoji}</span>
              <span className="lo-step-label">{step.label}</span>
            </li>
          ))}
        </ul>

        <div className="lo-progress-track">
          <div
            className="lo-progress-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}