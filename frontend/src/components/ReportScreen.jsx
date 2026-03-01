import { useState } from "react";
import { RISK, STATUS } from "../utils/constants";
import ChatPanel from "./ChatPanel";
import "../styles/ReportScreen.css";

/* ── Small reusable Box card ─────────────────────────────────────────────────── */
function Box({ title, children }) {
  return (
    <div className="report-box">
      <div className="report-box__title">{title}</div>
      {children}
    </div>
  );
}

export default function ReportScreen({ patient }) {
  const [openTest, setOpenTest] = useState(null);
  const [testTab, setTestTab]   = useState("all");
  const [chatOpen, setChatOpen] = useState(false);

  const rc       = RISK[patient.risk];
  const abnormal = patient.tests.filter((t) => t.status !== "Normal");
  const filtered =
    testTab === "all"      ? patient.tests
    : testTab === "abnormal" ? abnormal
    : patient.tests.filter((t) => t.cat === testTab);

  return (
    <div className="report-root">

      {/* ── Patient banner ─────────────────────────────────────────────────── */}
      <div className="report-banner">
        <div className="report-banner__avatar">{patient.initials}</div>
        <div className="report-banner__info">
          <div className="report-banner__name">{patient.name}</div>
          <div className="report-banner__meta">
            {patient.gender} · {patient.age} · ID {patient.id} · {patient.date}
          </div>
          <div className="report-banner__files">📎 {patient.files.join(", ")}</div>
        </div>
        <div
          className="report-banner__pill"
          style={{ background: rc.bg, border: `1px solid ${rc.border}` }}
        >
          <span className="report-banner__pill-dot" style={{ background: rc.dot }} />
          <span className="report-banner__pill-label" style={{ color: rc.color }}>
            {rc.label}
          </span>
        </div>
      </div>

      {/* ── Report grid ────────────────────────────────────────────────────── */}
      <div className="report-grid">

        {/* Left column */}
        <div className="report-col">
          <Box title="🧠 Plain-Language Summary">
            <div className="report-summary-accent">
              <p className="report-summary-text">{patient.summary}</p>
            </div>
          </Box>

          <Box title="📌 Key Highlights">
            {patient.highlights.map((h, i) => (
              <div key={i} className="report-highlight">
                <div className="report-highlight__dot" />
                <span className="report-highlight__text">{h}</span>
              </div>
            ))}
          </Box>

          <Box title="🔬 Recommended Next Steps">
            {patient.nextSteps.map((s, i) => (
              <div key={i} className="report-nextstep">
                <div className="report-nextstep__num">{i + 1}</div>
                <span className="report-nextstep__text">{s}</span>
              </div>
            ))}
          </Box>
        </div>

        {/* Right column */}
        <div className="report-col">

          {/* Stats row */}
          <div className="report-stats">
            {[
              { v: patient.tests.length,                                  l: "Total Tests", c: "#2563eb", bg: "#eff6ff", bc: "#bfdbfe" },
              { v: abnormal.length,                                        l: "Abnormal",    c: "#dc2626", bg: "#fff1f2", bc: "#fecdd3" },
              { v: patient.tests.filter((t) => t.status === "Normal").length, l: "Normal",  c: "#16a34a", bg: "#f0fdf4", bc: "#bbf7d0" },
            ].map((s) => (
              <div
                key={s.l}
                className="report-stat"
                style={{ background: s.bg, border: `1px solid ${s.bc}` }}
              >
                <div className="report-stat__value" style={{ color: s.c }}>{s.v}</div>
                <div className="report-stat__label">{s.l}</div>
              </div>
            ))}
          </div>

          {/* Test results box */}
          <Box title="📋 Test Results">
            <div className="report-test-tabs">
              {["all", "abnormal", "Blood", "X-Ray"].map((t) => (
                <button
                  key={t}
                  className={`report-test-tab${testTab === t ? " report-test-tab--active" : ""}`}
                  onClick={() => setTestTab(t)}
                >
                  {t === "all" ? "All" : t === "abnormal" ? "⚠ Abnormal" : t}
                </button>
              ))}
            </div>

            {filtered.map((t, i) => {
              const sc   = STATUS[t.status];
              const open = openTest === i;
              return (
                <div
                  key={i}
                  className="report-test-row"
                  style={{
                    borderColor: open ? sc.color + "50" : "#ece8e3",
                    background:  open ? sc.bg            : "#faf9f7",
                  }}
                  onClick={() => setOpenTest(open ? null : i)}
                >
                  <div className="report-test-row__top">
                    <div className="report-test-row__left">
                      <div
                        className="report-test-row__icon"
                        style={{ background: sc.bg, color: sc.color, borderColor: sc.border }}
                      >
                        {sc.icon}
                      </div>
                      <div>
                        <div className="report-test-row__name">{t.name}</div>
                        <div className="report-test-row__cat">{t.cat}</div>
                      </div>
                    </div>
                    <div className="report-test-row__right">
                      <div className="report-test-row__value" style={{ color: sc.color }}>
                        {t.value}{t.unit ? ` ${t.unit}` : ""}
                      </div>
                      <div className="report-test-row__ref">{t.ref}</div>
                    </div>
                    <span
                      className="report-test-row__chevron"
                      style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)" }}
                    >
                      ›
                    </span>
                  </div>

                  {open && (
                    <div className="report-test-expand">
                      <div className="report-test-expand__divider" />
                      <p className="report-test-expand__text">{t.note}</p>
                    </div>
                  )}
                </div>
              );
            })}

            <p className="report-tests-hint">Click any row to expand explanation</p>
          </Box>

          {/* Disclaimer */}
          <div className="report-disclaimer">
            <span>⚠️</span>
            <span className="report-disclaimer__text">
              AI analysis is for informational purposes only. Always consult a qualified healthcare professional.
            </span>
          </div>
        </div>
      </div>

      {/* ── Floating chat FAB ──────────────────────────────────────────────── */}
      <button
        className={`report-fab${chatOpen ? " report-fab--open" : ""}`}
        onClick={() => setChatOpen((o) => !o)}
      >
        <span className="report-fab__icon">{chatOpen ? "✕" : "💬"}</span>
        {!chatOpen && <span className="report-fab__label">Ask AI</span>}
      </button>

      {/* ── Floating chat panel ────────────────────────────────────────────── */}
      {chatOpen && (
        <div className="report-chat-float">
          <ChatPanel patient={patient} onClose={() => setChatOpen(false)} />
        </div>
      )}

    </div>
  );
}
