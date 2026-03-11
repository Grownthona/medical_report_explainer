import { useState } from "react";
import Navbar from "../components/Navbar";
import DropZone from "../components/DropZone";
import { LANGUAGES, FEATURE_PILLS } from "../utils/constants";
import "../styles/UploadPage.css";

export default function UploadPage({ onAnalyze }) {
  const [tab, setTab] = useState("upload");
  const [file, setFile] = useState(null);
  const [pasteText, setPasteText] = useState("");
  const [language, setLanguage] = useState("English");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const hasContent = file || pasteText.trim();

  const handleAnalyze = async () => {
    if (!hasContent || loading) return;

    setError(null);
    setLoading(true);

    try {
      let data;

      if (tab === "upload" && file) {
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("http://127.0.0.1:8000/extract/text", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server error: ${res.status}`);
        }

        data = await res.json();

      } else {
        const res = await fetch("http://127.0.0.1:8000/extract/text", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: pasteText }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server error: ${res.status}`);
        }

        data = await res.json();
      }

      onAnalyze(data, language);

    } catch (err) {
      setError(err.message || "Something went wrong.");

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-page">

      <Navbar />

      <div className="hero">

        <div className="badge">
          ✦ AI-POWERED MEDICAL TRANSLATOR
        </div>

        <h1 className="hero-title">
          Understand Your
          <br />
          <span className="gradient">
            Medical Report
          </span>
          <br />
          In Plain Language
        </h1>

        <p className="hero-sub">
          Upload any medical report — PDF, image, or text — and get an instant,
          easy-to-understand explanation with highlighted abnormal values.
        </p>

        {/* Feature pills */}
        <div className="feature-pills">
          {FEATURE_PILLS.map((f) => (
            <span key={f} className="pill">
              {f}
            </span>
          ))}
        </div>

        {/* Upload Card */}
        <div className="upload-card">

          {/* Tabs */}
          <div className="tabs">
            {["upload", "paste"].map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`tab ${tab === t ? "tab-active" : ""}`}
              >
                {t === "upload" ? "📄 Upload File" : "✏️ Paste Text"}
              </button>
            ))}
          </div>

          {/* Input */}
          {tab === "upload" ? (
            <DropZone file={file} onFileChange={setFile} />
          ) : (
            <textarea
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Paste your medical report text here..."
              className="paste-box"
            />
          )}

          {/* Footer */}
          <div className="upload-footer">

            <div className="language-select">
              <span>🌐 Language</span>

              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                {LANGUAGES.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>

            </div>

            <button
              onClick={handleAnalyze}
              disabled={!hasContent || loading}
              className="analyze-btn"
            >
              {loading ? "Analyzing…" : "✦ Analyze Report"}
            </button>

          </div>

          {error && (
            <div className="error-box">
              ⚠ {error}
            </div>
          )}

        </div>

      </div>
    </div>
  );
}