import { useState } from 'react'


import axios from "axios";
import UploadMedicalFile from '../components/UploadMedicalFile';
import TypingSummary from '../components/TypingSummary';
import '../App.css'

export default function Home() {

  
  const [files, setFiles] = useState([]);
  const [summary, setSummary] = useState("");
  const [advice, setAdvice] = useState("");
  const [loading, setLoading] = useState(false);
  const [tests_analysis, setAnalysis] = useState("");
  // const [risk_level, setRiskLevel] = useState("");
  // const [voice_script, setVoiceScript] = useState("");
  // const [response, setResponse] = useState("");

  const sendReport = async () => {
    setLoading(true);

    const formData = new FormData();
    files.forEach(file => formData.append("medicalFiles", file));
    try {
      const res = await axios.post(
        "http://localhost:5000/api/upload/multiple",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      console.log(res.data);
      alert("Files uploaded successfully");
      const summary = { title: "Summary", description:  res.data.summary};
      const advice = { title: "Advice", description: res.data.advice };
      const tests_analysis = { title: "Analysis", description: res.data.tests_analysis };
      setSummary(summary);
      setAdvice(advice);
      setAnalysis(tests_analysis);
      // setRiskLevel(JSON.stringify(res.data.risk_level, null, 2));
      // setVoiceScript(JSON.stringify(res.data.voice_script, null, 2));
      // setResponse(JSON.stringify(res.data.analysis, null, 2));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <>
      <div className="card">
        <div style={{ padding: 20 }}>
          <h1>Medical Report Translator</h1>
          <input
            type="file"
            className="custom-file-button"
            multiple
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={(e) => setFiles(Array.from(e.target.files))}
          />
          {/* <textarea
            rows="6"
            cols="60"
            placeholder="Paste medical report text..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          /> */}

          <br /><br />

          <button onClick={sendReport}>
            Analyze Report
          </button>
          {loading && summary && advice && (< TypingSummary summary={[summary, tests_analysis ,advice]} tests_analysis={tests_analysis} />)}
         
         
        </div>
        {/* <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button> */}
        
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

