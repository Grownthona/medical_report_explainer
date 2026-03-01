// ── Mock report analyzer ──────────────────────────────────────────────────────
// Replace this entire function body with a real API call, e.g.:
//   const form = new FormData();
//   files.forEach(f => form.append("files", f));
//   const res = await fetch("/api/analyze", { method: "POST", body: form });
//   return res.json();

let _counter = 0;

export async function analyzeFiles(files) {
  await new Promise((r) => setTimeout(r, 2700));
  _counter++;

  const names = ["Farah Rahman", "Arif Hossain", "Nadia Islam", "Karim Uddin", "Sumaiya Begum"];
  const name  = names[(_counter - 1) % names.length];
  const risks = ["Low", "Medium", "High"];
  const risk  = risks[(_counter - 1) % risks.length];
  const initials = name.split(" ").map((n) => n[0]).join("");

  return {
    id:       `PAT-${String(_counter).padStart(3, "0")}`,
    initials,
    name,
    risk,
    age:    `${42 + _counter * 3}Y`,
    gender: _counter % 2 === 0 ? "Male" : "Female",
    date:   new Date().toLocaleDateString("en-GB"),
    files:  files.map((f) => f.name),

    summary: `Report for ${name} shows ${
      risk === "Low"    ? "all values within normal range — no immediate concerns detected."
      : risk === "Medium" ? "some abnormal values requiring monitoring and specialist follow-up."
      : "several critical values outside safe limits — urgent clinical consultation recommended."
    }`,

    highlights: [
      risk !== "Low"
        ? "Elevated ESR (34 mm/1st hr) — suggests active inflammation."
        : "ESR within normal range.",
      "Uric acid (4.40 mg/dl) is within the normal female reference range.",
      risk === "High"
        ? "X-ray reveals spondylolisthesis L4/L5 — forward vertebral slip present."
        : "Lumbar disc spaces appear normal on X-ray.",
      "Bilateral sacroiliac joints show hazy outline — bilateral sacroiliitis noted.",
      "Osteophytes detected along lumbar vertebrae indicating degenerative changes.",
    ],

    nextSteps: [
      "Discuss all findings with your orthopaedic specialist for a comprehensive plan.",
      risk !== "Low"
        ? "MRI of lumbar spine recommended to assess soft tissue and nerves."
        : "Routine follow-up in 6 months.",
      "Physical therapy and anti-inflammatory medication may be prescribed.",
      "Periodic monitoring of uric acid alongside kidney function is advised.",
    ],

    tests: [
      { name: "Uric Acid",               value: "4.40",                        unit: "mg/dl", ref: "F: 2.4–5.7", status: "Normal",                            cat: "Blood", note: "Within healthy range. No current risk of gout or uric acid kidney stones." },
      { name: "ESR",                     value: risk !== "Low" ? "34" : "18",   unit: "mm/hr", ref: "F: 0–25",    status: risk !== "Low" ? "High" : "Normal",   cat: "Blood", note: "ESR measures red blood cell sedimentation rate. Elevated values signal general inflammation or infection." },
      { name: "Osteophytes",             value: "Present",                      unit: "",      ref: "Absent",      status: "Abnormal",                           cat: "X-Ray", note: "Bone spurs along lumbar vertebrae indicate degenerative wear. May compress nearby nerves." },
      { name: "Sacralization L5–S1",     value: "Present",                      unit: "",      ref: "Absent",      status: "Abnormal",                           cat: "X-Ray", note: "Congenital fusion variant. Usually asymptomatic but can alter spinal mechanics." },
      { name: "Spondylolisthesis L4/L5", value: "Forward Slip",                 unit: "",      ref: "No Slip",     status: risk === "High" ? "High" : "Abnormal", cat: "X-Ray", note: "L4 has slipped forward over L5 — may range from mild backache to nerve compression." },
      { name: "Lumbar Disc Spaces",      value: "Normal",                       unit: "",      ref: "Normal",      status: "Normal",                             cat: "X-Ray", note: "Disc heights are preserved. Discs are not significantly degenerated at this stage." },
      { name: "Sacroiliac Joints",       value: "Hazy Outline",                 unit: "",      ref: "Clear",       status: risk === "High" ? "High" : "Abnormal", cat: "X-Ray", note: "Bilateral haziness indicates sacroiliitis — inflammation causing lower back and buttock pain." },
    ],
  };
}