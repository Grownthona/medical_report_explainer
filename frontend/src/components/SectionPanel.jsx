import "../styles/SectionPanel.css";
import { useState } from "react";
import { RISK_CONFIG } from "../utils/constants";
import TestCard from "./TestCard";
import VoiceExplainer from "./VoiceExplainer";

export default function SectionPanel({ sectionIndex, section, language }) {
  const risk = RISK_CONFIG[section.risk_level] || RISK_CONFIG.Low;
  const [open, setOpen] = useState(false);

  return (
    <div key={sectionIndex}>
      
      {/* ── Section title header ── */}

      <div className={`section-title-header ${open ? "section-title-header-open" : ""}`} onClick={() => setOpen(!open)}>
        <p className="section-index-label">Report</p>
        <div className="section-title-row">
          <div className="section-number">{sectionIndex + 1}</div>
          <div className="section-vline" />
          <h2 className="section-title-text">
            {section.section_title || "Report"}
          </h2>
        </div>
      </div>
       {/* ── Collapsible body ── */}

      {open && (
        <div className="section-body">
          {/* Voice Explainer Section */}
          {section.voice_explanation && (
            <VoiceExplainer text={section.voice_explanation} lang={language}/>
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
              <div className={`section-chevron ${open ? "section-chevron-open" : ""}`}>

                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">

                  <path d="M4 6l4 4 4-4" stroke="#64748b" strokeWidth="1.8"

                    strokeLinecap="round" strokeLinejoin="round"/>

                </svg>

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
      </div>)}
    </div>
  );
}