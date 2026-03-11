import { useState } from "react";
import { getStatus } from "../utils/getStatus";
import "../styles/TestCard.css";

export default function TestCard({ test }) {
  const [open, setOpen] = useState(false);
  const st = getStatus(test.status);

  return (
    <div
      className={`test-card ${open ? "test-card-open" : ""}`}
      style={{
        "--status-color": st.color,
        "--status-border": st.border,
        "--status-bg": st.bg,
      }}
      onClick={() => setOpen(!open)}
    >
      {open && <div className="test-card-glow" />}

      {/* Header */}
      <div className="test-card-header">
        <div className="test-card-left">

          <div className="test-card-indicator" />

          <div className="test-card-info">
            <div className="test-card-title">
              {test.test_name}
            </div>

            {test.value !== "" && (
              <div className="test-card-meta">

                <span className="test-card-value">
                  {test.value}
                  <span className="test-card-unit">{test.unit}</span>
                </span>

                <span className="test-card-divider">|</span>

                <span className="test-card-ref">
                  Ref: {test.reference_range}
                </span>

              </div>
            )}
          </div>
        </div>

        <div className="test-card-right">

          <span className="test-card-badge">
            {st.label}
          </span>

          <div className={`test-card-chevron ${open ? "rotate" : ""}`}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path
                d="M4 6l4 4 4-4"
                stroke="#94a3b8"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

        </div>
      </div>

      {open && (
        <div className="test-card-expanded">

          <div className="test-card-grid">

            {/* What is this test */}
            <div className="test-card-box">

              <div className="test-card-box-title">
                🔬
                <span>What is this test?</span>
              </div>

              <p className="test-card-text">
                {test.keyword_explanation}
              </p>

            </div>

            {/* Result */}
            <div className="test-card-box result-box">

              <div className="test-card-box-title result-title">
                <div className="result-dot" />
                <span>Your Result</span>
              </div>

              <p className="test-card-text result-text">
                {test.result_explanation}
              </p>

            </div>

          </div>

        </div>
      )}
    </div>
  );
}