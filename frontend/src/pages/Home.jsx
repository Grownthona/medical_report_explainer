import { useState } from 'react'
import LangSelector from '../components/LangSelector';
import UploadTabBtn    from "../components/UploadTabBtn";
import WelcomeScreen   from "../components/WelcomeScreen";
import AnalyzingScreen from "../components/AnalyzingScreen";
import ReportScreen    from "../components/ReportScreen";
import { analyzeFiles } from "../utils/analyzeFiles";
import { RISK } from "../utils/constants";
import "../styles/global.css";
import "../styles/AppShell.css";

export default function Home() {
  const [patients,   setPatients]   = useState([]);
  const [activeId,   setActiveId]   = useState(null);
  const [busy,       setBusy]       = useState(false);
  const [busyFiles,  setBusyFiles]  = useState([]);
  const [lang,       setLang]       = useState("en");

  const handleUpload = async (files) => {
    setBusyFiles(files);
    setBusy(true);
    try {
      const report = await analyzeFiles(files);
      setPatients((p) => [...p, report]);
      setActiveId(report.id);
    } finally {
      setBusy(false);
    }
  };

  const closePatient = (id) => {
    setPatients((p) => {
      const next = p.filter((x) => x.id !== id);
      if (activeId === id) setActiveId(next.length ? next[next.length - 1].id : null);
      return next;
    });
  };

  const active = patients.find((p) => p.id === activeId);

  return (
    <div className="app-root">

      {/* ── App Bar ──────────────────────────────────────────────────────── */}
      <header className="app-bar">

        {/* Brand */}
        <div className="app-brand">
          <span className="app-brand__icon">⚕</span>
          <span className="app-brand__text">
            Medi<span className="app-brand__blue">Translate</span>
          </span>
          <span className="app-brand__badge">AI</span>
        </div>

        {/* Patient tabs */}
        <div className="app-tabs-wrap">
          {patients.map((p) => {
            const rc = RISK[p.risk];
            const on = p.id === activeId;
            return (
              <button
                key={p.id}
                className={`app-tab${on ? " app-tab--active" : ""}`}
                onClick={() => setActiveId(p.id)}
              >
                <div className={`app-tab__avatar${on ? " app-tab__avatar--active" : " app-tab__avatar--idle"}`}>
                  {p.initials}
                </div>
                <div className="app-tab__body">
                  <span className={`app-tab__name${on ? " app-tab__name--active" : " app-tab__name--idle"}`}>
                    {p.name}
                  </span>
                  <span className="app-tab__risk" style={{ color: rc.color }}>
                    {p.risk} Risk
                  </span>
                </div>
                <span
                  className="app-tab__close"
                  style={{ opacity: on ? 0.6 : 0.3 }}
                  onClick={(e) => { e.stopPropagation(); closePatient(p.id); }}
                >
                  ×
                </span>
                {on && <div className="app-tab__indicator" />}
              </button>
            );
          })}

          {!busy ? (
            <UploadTabBtn onFiles={handleUpload} />
          ) : (
            <div className="app-busy-tab">
              <div className="app-busy-tab__spinner" />
              <span className="app-busy-tab__label">Analyzing…</span>
            </div>
          )}
        </div>

        {/* Right side: language + count */}
        <div className="app-bar-right">
          <LangSelector lang={lang} setLang={setLang} />
          <span className="app-bar-right__divider" />
          <span className="app-bar-right__count">
            {patients.length} patient{patients.length !== 1 ? "s" : ""}
          </span>
        </div>

      </header>

      {/* ── Body ─────────────────────────────────────────────────────────── */}
      <div className="app-body">
        {busy && patients.length === 0 ? (
          <AnalyzingScreen files={busyFiles} />
        ) : !active ? (
          <WelcomeScreen onFiles={handleUpload} lang={lang} setLang={setLang} />
        ) : (
          <ReportScreen key={active.id} patient={active} />
        )}
      </div>

    </div>
  );
}
