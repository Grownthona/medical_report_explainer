import { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import PatientCard from "../components/PatientCard";
import LanguageBadge from "../components/LanguageBadge";
import SectionTabs from "../components/SectionTabs";
import SectionPanel from "../components/SectionPanel";
import ChatBot from "../components/ChatBot";

export default function ResultsPage({ data, language, onBack }) {
  const [activePatientIndex, setActivePatientIndex] = useState(0);
  
  // Get current patient data
  const currentData = data.is_multi_patient 
    ? data.patients[activePatientIndex] 
    : data;

  const isMixed = currentData.is_mixed;
  const sections = currentData.sections || {};
  const sectionKeys = isMixed ? Object.keys(sections) : ["REPORT"];

  const [activeTab, setActiveTab] = useState(sectionKeys[0]);

  // Reset active tab when patient changes
  useEffect(() => {
    setActiveTab(isMixed ? Object.keys(currentData.sections || {})[0] : "REPORT");
  }, [activePatientIndex, isMixed, currentData.sections]);

  // Get active section data
  // In the new JSON, sections[activeTab] is an array (e.g., data.sections.LAB: [...])
  const activeSection = isMixed 
    ? (Array.isArray(sections[activeTab]) ? sections[activeTab][0] : sections[activeTab])
    : currentData.report;

  return (
    <div style={{ minHeight: "100vh", background: "#070d1a", color: "#f1f5f9" }}>
      <Navbar onBack={onBack} />

      <div style={{ maxWidth: 860, margin: "0 auto", padding: "32px 24px 100px" }}>
        
        {/* Multi-Patient Selector */}
        {data.is_multi_patient && (
          <div className="patient-selector" style={{ marginBottom: "20px", display: "flex", gap: "10px", overflowX: "auto", paddingBottom: "10px" }}>
            {data.patients.map((p, idx) => (
              <button
                key={idx}
                onClick={() => setActivePatientIndex(idx)}
                style={{
                  padding: "8px 16px",
                  borderRadius: "20px",
                  border: "1px solid",
                  borderColor: activePatientIndex === idx ? "#6366f1" : "rgba(255,255,255,0.1)",
                  background: activePatientIndex === idx ? "rgba(99, 102, 241, 0.1)" : "transparent",
                  color: activePatientIndex === idx ? "#818cf8" : "#94a3b8",
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                  transition: "all 0.2s"
                }}
              >
                👤 {p.patient.name || `Patient ${idx + 1}`}
              </button>
            ))}
          </div>
        )}

        <PatientCard patient={currentData.patient} summary={currentData.summary} />

        <LanguageBadge language={language} />

        <SectionTabs
          keys={sectionKeys}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {activeSection && (
          <div key={`${activePatientIndex}-${activeTab}`}>
            {isMixed && Array.isArray(sections[activeTab]) ? (
              sections[activeTab].map((s, i) => (
                <SectionPanel key={i} sectionIndex={i} section={s} language={language} />
              ))
            ) : (
              <SectionPanel sectionIndex={0} section={activeSection} language={language} />
            )}
          </div>
        )}
      </div>

      {/* Floating chat — always mounted, manages its own open/close state */}
      <ChatBot patientData={currentData} />
    </div>
  );
}