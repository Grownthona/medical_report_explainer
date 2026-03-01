// ── Shared constants ──────────────────────────────────────────────────────────

export const ACCEPTED = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
export const MAX_MB = 20;

export const STEPS = [
  "Reading document structure…",
  "Extracting test values…",
  "Mapping reference ranges…",
  "Generating plain-language report…",
];

export const LANGUAGES = [
  { code: "en", label: "English",   flag: "🇺🇸" },
  { code: "bn", label: "বাংলা",     flag: "🇧🇩" },
  { code: "ar", label: "العربية",   flag: "🇸🇦" },
  { code: "hi", label: "हिन्दी",    flag: "🇮🇳" },
  { code: "fr", label: "Français",  flag: "🇫🇷" },
  { code: "es", label: "Español",   flag: "🇪🇸" },
  { code: "zh", label: "中文",       flag: "🇨🇳" },
  { code: "pt", label: "Português", flag: "🇧🇷" },
];

export const RISK = {
  Low:    { color: "#16a34a", bg: "#dcfce7", border: "#bbf7d0", dot: "#22c55e", label: "LOW RISK" },
  Medium: { color: "#d97706", bg: "#fef3c7", border: "#fde68a", dot: "#f59e0b", label: "MODERATE RISK" },
  High:   { color: "#dc2626", bg: "#fee2e2", border: "#fecaca", dot: "#ef4444", label: "HIGH RISK" },
};

export const STATUS = {
  Normal:   { color: "#15803d", bg: "#f0fdf4", border: "#bbf7d0", icon: "✓" },
  Abnormal: { color: "#b45309", bg: "#fffbeb", border: "#fde68a", icon: "!" },
  High:     { color: "#b91c1c", bg: "#fff1f2", border: "#fecdd3", icon: "↑" },
};

export const QUICK_PROMPTS = [
  "What's most concerning?",
  "Explain the ESR result",
  "Is this serious?",
  "What causes back pain?",
];