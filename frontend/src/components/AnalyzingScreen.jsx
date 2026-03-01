import { useState, useEffect } from "react";
import { STEPS } from "../utils/constants";
import "../styles/AnalyzingScreen.css";

export default function AnalyzingScreen({ files }) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const t = setInterval(
      () => setStep((s) => Math.min(s + 1, STEPS.length - 1)),
      620
    );
    return () => clearInterval(t);
  }, []);

  const fileIcon = files[0]?.type === "application/pdf" ? "📑" : "🖼";

  return (
    <div className="analyzing-root">
      <div className="analyzing-card">

        {/* Document scan animation */}
        <div className="analyzing-scan-box">
          <span className="analyzing-scan-box__icon">{fileIcon}</span>
          <div className="analyzing-scan-box__line" />
          <div className="analyzing-scan-box__corner analyzing-scan-box__corner--tl" />
          <div className="analyzing-scan-box__corner analyzing-scan-box__corner--br" />
        </div>

        {/* Spinner */}
        <div className="analyzing-spinner-wrap">
          <div className="analyzing-spinner-ring" />
        </div>

        <div className="analyzing-title">Analyzing Report</div>
        <div className="analyzing-filename">{files.map((f) => f.name).join(", ")}</div>

        {/* Step list */}
        <div className="analyzing-steps">
          {STEPS.map((s, i) => {
            const state = i < step ? "done" : i === step ? "current" : "pending";
            return (
              <div
                key={i}
                className="analyzing-step"
                style={{ opacity: i <= step ? 1 : 0.2 }}
              >
                <span className={`analyzing-step__dot analyzing-step__dot--${state}`} />
                <span className={`analyzing-step__text analyzing-step__text--${state}`}>{s}</span>
              </div>
            );
          })}
        </div>

        {/* Progress bar */}
        <div className="analyzing-track">
          <div className="analyzing-fill" />
        </div>

      </div>
    </div>
  );
}
