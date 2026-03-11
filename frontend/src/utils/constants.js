export const LANGUAGES = ["English", "বাংলা", "हिंदी", "Arabic", "Spanish", "French", "Portuguese"];

export const STATUS_CONFIG = {
  Normal:  { color: "#22c55e", bg: "rgba(34,197,94,0.08)",   border: "rgba(34,197,94,0.25)",  label: "Normal"   },
  High:    { color: "#f97316", bg: "rgba(249,115,22,0.08)",  border: "rgba(249,115,22,0.3)",  label: "High ↑"   },
  Low:     { color: "#60a5fa", bg: "rgba(96,165,250,0.08)",  border: "rgba(96,165,250,0.3)",  label: "Low ↓"    },
  Abnormal:{ color: "#f43f5e", bg: "rgba(244,63,94,0.08)",   border: "rgba(244,63,94,0.3)",   label: "Abnormal" },
  Unknown: { color: "#94a3b8", bg: "rgba(148,163,184,0.08)", border: "rgba(148,163,184,0.2)", label: "Review"   },
};

export const RISK_CONFIG = {
  Low:    { color: "#22c55e", label: "Low Risk"    },
  Medium: { color: "#f97316", label: "Medium Risk" },
  High:   { color: "#f43f5e", label: "High Risk"   },
};

export const TAB_ICONS = { LAB: "🧪", IMAGING: "🩻", REPORT: "📋" };

export const FEATURE_PILLS = [
  "🤖 AI Explanation",
  "🔊 Voice Playback",
  "⚠️ Abnormal Values",
  "🌐 Multi-language",
];

export const GLOBAL_STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
  @keyframes fadeIn { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
  @keyframes pulse  { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
  * { box-sizing: border-box; }
  body { margin: 0; }
  select option { background: #0f172a; }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }
`;
