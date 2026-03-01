import { useState } from 'react'


import axios from "axios";
import UploadMedicalFile from '../components/UploadMedicalFile';
import TypingSummary from '../components/TypingSummary';
import '../App.css'

export default function Home() {

  
  const [files, setFiles] = useState([]);
  const [reports, setReports] = useState([]);

  const [loading, setLoading] = useState(false);
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
      if (res.data.success) {
        setReports(res.data.processed); // store full array
        alert("Files processed successfully");
      }
      // const summary = { title: "Summary", description:  res.data.summary};
      // const advice = { title: "Advice", description: res.data.advice };
      // const tests_analysis = { title: "Analysis", description: res.data.tests_analysis };
      // setSummary(summary);
      // setAdvice(advice);
      // setAnalysis(tests_analysis);
      // // setRiskLevel(JSON.stringify(res.data.risk_level, null, 2));
      // // setVoiceScript(JSON.stringify(res.data.voice_script, null, 2));
      // // setResponse(JSON.stringify(res.data.analysis, null, 2));
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
          {/* {loading && summary && advice && (< TypingSummary summary={[summary, tests_analysis ,advice]} tests_analysis={tests_analysis} />)} */}

           {loading && reports.map((report, index) => (
          <div key={index} className="report-card">
            <h2>{report.filename}</h2>

            {report.success ? (
              <>
                <h3>Summary</h3>
                <p>{report.summary}</p>

                <h3>Tests Analysis</h3>

                {report.tests_analysis?.map((test, i) => (
                  <div key={i} className="test-card">
                    <h4>{test.test_name}</h4>

                    <p>
                      <strong>Result:</strong> {test.value} {test.unit}
                    </p>

                    <p>
                      <strong>Reference Range:</strong> {test.reference_range}
                    </p>

                    <p>
                      <strong>Status:</strong>{" "}
                      <span
                        style={{
                          color:
                            test.status === "High"
                              ? "red"
                              : test.status === "Low"
                              ? "orange"
                              : "green"
                        }}
                      >
                        {test.status}
                      </span>
                    </p>

                    <p>
                      <strong>Explanation:</strong> {test.result_explanation}
                    </p>

                    <p>
                      <strong>Keyword Info:</strong> {test.keyword_explanation}
                    </p>

                    <hr />
                  </div>
                ))}
              </>
            ) : (
              <p style={{ color: "red" }}>Error: {report.error}</p>
            )}
          </div>
        ))}
         
         
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

