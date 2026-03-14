import "../styles/PatientCard.css";

export default function PatientCard({ patient, summary = {} }) {

  if (!patient || Object.keys(patient).length === 0) {
    return <div className="patient-card">No patient data available</div>;
  }

  const stats = [
    { label: "Total Tests", value: summary?.total_tests || 0, color: "#6366f1" },
    {
      label: "Abnormal",
      value: summary?.abnormal_count || 0,
      color: (summary?.abnormal_count || 0) > 0 ? "#f97316" : "#22c55e",
    },
    {
      label: "Critical",
      value: summary?.critical_count || 0,
      color: summary?.has_critical ? "#f43f5e" : "#22c55e",
    },
  ];

  return (
    <div className="patient-card">
      {/* Patient info */}
      <div className="patient-info">
        <div className="patient-label">Patient</div>

        <div className="patient-name">{patient?.name}</div>

        <div className="patient-meta">
          {patient?.age_years}y · {patient?.gender} · {patient?.collection_date}
        </div>
      </div>

      {/* Stats */}
      <div className="patient-stats">
        {stats.map((s) => (
          <div key={s?.label} className="stat-box">
            <div
              className="stat-value"
              style={{ color: s.color }}
            >
              {s?.value}
            </div>

            <div className="stat-label">{s?.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}