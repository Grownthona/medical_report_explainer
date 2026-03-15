import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import DropZone from "../components/DropZone";
import { LANGUAGES, FEATURE_PILLS } from "../utils/constants";
//import { MOCK_SAMPLES } from "../data/mockData";
import LoadingOverlay from "../components/LoadingOverlay";
import "../styles/UploadPage.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export default function UploadPage({ onAnalyze }) {
  const navigate = useNavigate();
  const [tab, setTab] = useState("upload");
  const [files, setFiles] = useState([]);

  const [pasteText, setPasteText] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const hasContent = files.length > 0 || pasteText.trim();

  const handleFiles = (newFiles) => {
    setFiles((prev) => {
      const merged = [...prev, ...newFiles];

      const unique = merged.filter(
        (file, index, self) =>
          index === self.findIndex((f) => f.name === file.name)
      );

      return unique;
    });
  };

  const handleAnalyze = async () => {
    if (!hasContent || loading) return;

    setError(null);
    setLoading(true);

    try {
      let data;

      if (tab === "upload" && files) {
        const formData = new FormData();
        files.forEach((file) => {
          formData.append("files", file);
        });
        formData.append("language", language);

        const res = await fetch(`${API_BASE}/extract/file`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server error: ${res.status}`);
        }

        data = await res.json();
      } else {
        const formData = new FormData();
        formData.append("text", pasteText);
        formData.append("language", language);

        const res = await fetch(`${API_BASE}/extract/text`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Server error: ${res.status}`);
        }

        data = await res.json();
      }

      if (onAnalyze) onAnalyze(data, language);
      navigate("/results", { state: { reportData: data, language: language } });
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-page">
      <LoadingOverlay visible={loading} />
      <Navbar />

      <div className="hero">
        <div className="badge">✦ AI-POWERED MEDICAL TRANSLATOR</div>

        <h1 className="hero-title">
          Understand Your
          <br />
          <span className="gradient">Medical Report</span>
          <br />
          In Plain Language
        </h1>

        <p className="hero-sub" style={{ marginTop: 20 }}>
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
            <DropZone files={files} onFileChange={handleFiles} />
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
                {Object.entries(LANGUAGES).map(([name, code]) => (
                  <option key={code} value={code}>
                    {name}
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