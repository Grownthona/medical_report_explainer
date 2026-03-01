import { useState, useRef, useEffect } from "react";
import { LANGUAGES } from "../utils/constants";
import "../styles/LangSelector.css";

export default function LangSelector({ lang, setLang, invert = false }) {
  const [open, setOpen] = useState(false);
  const ref = useRef();
  const cur = LANGUAGES.find((l) => l.code === lang);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const triggerClass = [
    "lang-selector__trigger",
    invert ? "lang-selector__trigger--invert" : "",
    open   ? "lang-selector__trigger--open"   : "",
  ].filter(Boolean).join(" ");

  return (
    <div ref={ref} className="lang-selector">
      <button className={triggerClass} onClick={() => setOpen((o) => !o)}>
        <span className="lang-selector__flag">{cur.flag}</span>
        <span
          className="lang-selector__label"
          style={{ color: invert ? "#fff" : "#374151" }}
        >
          {cur.label}
        </span>
        <span
          className="lang-selector__chevron"
          style={{
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            color: invert ? "rgba(255,255,255,0.6)" : "#94a3b8",
          }}
        >
          ▾
        </span>
      </button>

      {open && (
        <div className="lang-selector__dropdown">
          <div className="lang-selector__dropdown-header">Report Language</div>
          {LANGUAGES.map((l) => (
            <button
              key={l.code}
              className={`lang-selector__option${lang === l.code ? " lang-selector__option--selected" : ""}`}
              onClick={() => { setLang(l.code); setOpen(false); }}
            >
              <span className="lang-selector__opt-flag">{l.flag}</span>
              <span className="lang-selector__opt-label">{l.label}</span>
              {lang === l.code && <span className="lang-selector__opt-check">✓</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
