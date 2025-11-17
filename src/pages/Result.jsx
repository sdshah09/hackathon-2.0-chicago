import React, { useState, useEffect } from "react";
import { jsPDF } from "jspdf";
import "../styles/result.css";

const Result = () => {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    const fakeData = {
      diagnosis: ["Hypertension Stage 2", "High Cholesterol"],
      medications: ["Amlodipine 5mg", "Atorvastatin 20mg"],
      labs: ["BP: 150/95", "Cholesterol: 260 mg/dL"],
      keyFindings: ["High cardiovascular risk", "Long-term BP elevation"],
    };

    setTimeout(() => {
      setSummary(fakeData);
    }, 1000);
  }, []);

  const downloadPDF = () => {
    const doc = new jsPDF();
    doc.text("AI Medical Summary", 10, 10);
    doc.save("summary.pdf");
  };

  if (!summary) return <p>Loading...</p>;

  return (
    <div className="result-container">
      <h1>AI Medical Summary</h1>

      {Object.entries(summary).map(([title, list]) => (
        <div className="section" key={title}>
          <h2>{title}</h2>
          <ul>
            {list.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </div>
      ))}

      <button className="download-btn" onClick={downloadPDF}>
        Download PDF
      </button>
    </div>
  );
};

export default Result;
