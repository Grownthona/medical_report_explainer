import { useState } from "react";
import UploadPage from "./UploadPage";
import ResultsPage from "./ResultsPage";
import { GLOBAL_STYLES } from "../utils/constants";

export default function Home() {
  const [page, setPage] = useState("upload");
  const [reportData, setReportData] = useState(null);
  const [language, setLanguage] = useState("English");

  const handleAnalyze = (data, lang) => {
    setReportData(data);
    setLanguage(lang);
    setPage("results");
  };

  const handleBack = () => {
    setPage("upload");
    setReportData(null);
  };

  return (
    <>
      <style>{GLOBAL_STYLES}</style>

      {page === "results" && reportData ? (
        <ResultsPage data={reportData} language={language} onBack={handleBack} />
      ) : (
        <UploadPage onAnalyze={handleAnalyze} />
      )}
    </>
  );
}