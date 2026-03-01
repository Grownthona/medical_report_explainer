// ── Chat reply logic ──────────────────────────────────────────────────────────
// Replace getChatReply() with a real LLM API call, passing the patient report
// as system context for accurate, report-specific answers.

const RESPONSES = {
  uric:    "Uric acid at 4.40 mg/dl is perfectly normal for a female patient (reference: 2.4–5.7 mg/dl). No dietary changes or treatment are currently indicated based on this value alone.",
  esr:     "An elevated ESR of 34 mm/hr (above the normal 0–25 range) suggests some inflammation is present in the body. It's a non-specific marker — your doctor will correlate it with symptoms and other tests to find the cause.",
  pain:    "The combination of spondylolisthesis (L4 slipping over L5) and sacroiliitis can both contribute to lower back and leg pain. Physical therapy and anti-inflammatory medications are common first-line treatments.",
  serious: "The most significant findings are the forward slip of L4 over L5 and the bilateral sacroiliitis. These warrant follow-up with an orthopaedic specialist, but many patients manage these conditions well with conservative treatment.",
  default: (q) => `Thank you for your question about "${q.slice(0, 40)}${q.length > 40 ? "…" : ""}". Based on this report, I can help explain any specific findings. Please note this is informational only — always consult your doctor for medical advice.`,
};

export function getChatReply(msg) {
  const m = msg.toLowerCase();
  if (m.includes("uric"))                                               return RESPONSES.uric;
  if (m.includes("esr") || m.includes("inflamm"))                       return RESPONSES.esr;
  if (m.includes("pain") || m.includes("hurt") || m.includes("ache"))  return RESPONSES.pain;
  if (m.includes("serious") || m.includes("worry") || m.includes("concern") || m.includes("bad"))
    return RESPONSES.serious;
  return RESPONSES.default(msg);
}