import { useRef, useState } from "react";
import { ACCEPTED, MAX_MB, LANGUAGES } from "../utils/constants";
import LangSelector from "./LangSelector";
import "../styles/WelcomeScreen.css";

export default function WelcomeScreen({ onFiles, lang, setLang }) {
  const ref = useRef();
  const [drag, setDrag] = useState(false);
  const [err, setErr]   = useState("");

  const cur = LANGUAGES.find((l) => l.code === lang);

  const go = (files) => {
    const arr = Array.from(files);
    const bad = arr.find((f) => !ACCEPTED.includes(f.type));
    if (bad) { setErr(`"${bad.name}" is not a supported format.`); return; }
    const big = arr.find((f) => f.size > MAX_MB * 1024 * 1024);
    if (big) { setErr(`"${big.name}" exceeds ${MAX_MB}MB.`); return; }
    setErr("");
    onFiles(arr);
  };

  return (
    <div className="welcome-root">
      {/* Decorative blobs */}
      <div className="welcome-blob welcome-blob--1" />
      <div className="welcome-blob welcome-blob--2" />
      <div className="welcome-blob welcome-blob--3" />

      {/* Full-width frosted card */}
      <div className="welcome-card">

        {/* Top row: AI badge + language selector */}
        <div className="welcome-top-row">
          <div className="welcome-badge">
            <span className="welcome-badge__dot" />
            <span className="welcome-badge__text">AI-Powered Medical Analysis</span>
          </div>
          <div className="welcome-lang-row">
            <span className="welcome-lang-prefix">🌐 Report in:</span>
            <LangSelector lang={lang} setLang={setLang} />
          </div>
        </div>

        {/* Hero headline */}
        <div className="welcome-hero">
          <h1 className="welcome-title">
            Understand your<br />
            <span className="welcome-title__grad">medical reports</span>
          </h1>
          <p className="welcome-subtitle">
            Upload any lab result or X-ray. Get an instant plain-language breakdown
            in {cur.label} — no medical degree needed.
          </p>
        </div>

        {/* Drop zone */}
        <div
          className={`welcome-drop${drag ? " welcome-drop--drag" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => { e.preventDefault(); setDrag(false); go(e.dataTransfer.files); }}
          onClick={() => ref.current.click()}
        >
          <input
            ref={ref}
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.webp,.pdf"
            style={{ display: "none" }}
            onChange={(e) => go(e.target.files)}
          />

          <div className={`welcome-drop__icon-circle${drag ? " welcome-drop__icon-circle--drag" : ""}`}>
            <span className="welcome-drop__icon">{drag ? "📥" : "📂"}</span>
          </div>

          <div className="welcome-drop__title">
            {drag ? "Release to analyze" : "Drop your report here"}
          </div>

          <div className="welcome-drop__or">
            <span className="welcome-drop__or-line" />
            <span className="welcome-drop__or-text">or</span>
            <span className="welcome-drop__or-line" />
          </div>

          <div className="welcome-browse-btn">Browse Files</div>
          <div className="welcome-drop__limit">
            JPG · PNG · WebP · PDF &nbsp;·&nbsp; Max {MAX_MB}MB
          </div>
        </div>

        {/* Validation error */}
        {err && <div className="welcome-error">⚠ {err}</div>}

        {/* Feature pills */}
        <div className="welcome-feats">
          {[
            ["🔒", "Private & Secure"],
            ["⚡", "Instant Results"],
            ["🌐", "8 Languages"],
            ["🩺", "Plain Language"],
          ].map(([icon, label]) => (
            <div key={label} className="welcome-feat">
              <span>{icon}</span>
              <span className="welcome-feat__label">{label}</span>
            </div>
          ))}
        </div>

        <p className="welcome-disclaimer">
          ⚠ For informational purposes only. Always consult a qualified healthcare professional.
        </p>

      </div>
    </div>
  );
}
