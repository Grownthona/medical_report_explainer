import { useState } from "react";
import Navbar from "../components/Navbar";
import PatientCard from "../components/PatientCard";
import LanguageBadge from "../components/LanguageBadge";
import SectionTabs from "../components/SectionTabs";
import SectionPanel from "../components/SectionPanel";
import ChatBot from "../components/ChatBot";

export default function ResultsPage({ data, language, onBack }) {
  const isMixed = data.is_mixed;
  const sectionKeys = isMixed ? Object.keys(data.sections || {}) : ["REPORT"];

  const [activeTab, setActiveTab] = useState(sectionKeys[0]);

  const activeSection = isMixed ? data.sections[activeTab]?.[0] : data.report;

  return (
    <div style={{ minHeight: "100vh", background: "#070d1a", color: "#f1f5f9" }}>
      <Navbar onBack={onBack} />

      <div style={{ maxWidth: 860, margin: "0 auto", padding: "32px 24px 100px" }}>
        <PatientCard patient={data.patient} summary={data.summary} />

        <LanguageBadge language={language} />

        <SectionTabs
          keys={sectionKeys}
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />

        {activeSection && <SectionPanel section={activeSection} />}
      </div>

      {/* Floating chat — always mounted, manages its own open/close state */}
      <ChatBot patientData={data} />
    </div>
  );
}