import "../styles/SectionPanel.css";
import { RISK_CONFIG } from "../utils/constants";
import TestCard from "./TestCard";
import VoiceExplainer from "./VoiceExplainer";

export default function SectionPanel({ section }) {
  const risk = RISK_CONFIG[section.risk_level] || RISK_CONFIG.Low;

  return (
    <div>
      {/* Voice Explainer Section */}
      {section.voice_explanation && (
        <VoiceExplainer text={section.voice_explanation} />
      )}
      {/* Summary card */}
      <div className="section-summary-card">
        <div className="summary-glow"></div>

        <div className="summary-row">
          <div className="summary-text">
            <div className="summary-label-row">
              <div className="summary-line"></div>

              <span className="summary-label">
                Summary
              </span>
            </div>

            <p className="summary-description">
              {section.summary}
            </p>
          </div>

          {/* Risk badge */}
          <div
            className="risk-badge"
            style={{
              color: risk.color,
              borderColor: `${risk.color}35`,
              background: `${risk.color}12`,
              boxShadow: `0 0 16px ${risk.color}20`,
            }}
          >
            ⚡ {risk.label}
          </div>
        </div>
      </div>

      {/* Tests header */}
      <div className="tests-header">
        <div className="tests-line"></div>

        <span className="tests-title">
          {section.tests_analysis?.length || 0} Tests · Click to expand
        </span>
      </div>

      {section.tests_analysis?.map((test, i) => (
        <TestCard key={i} test={test} />
      ))}

      {/* Advice */}
      {section.advice && (
        <div className="advice-card">
          <div className="advice-glow"></div>

          <div className="advice-header">
            <div className="advice-icon">💡</div>

            <span className="advice-title">
              Advice
            </span>
          </div>

          <p className="advice-text">
            {section.advice}
          </p>
        </div>
      )}
    </div>
  );
}