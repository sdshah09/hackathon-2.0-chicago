import React, { useState } from "react";
import "../styles/upload.css";

const Upload = () => {
  const [category, setCategory] = useState("");
  const [files, setFiles] = useState([]);

  const handleFiles = (e) => {
    const selectedFiles = Array.from(e.target.files);

    // Add uploaded files without removing the existing ones
    setFiles((prev) => [...prev, ...selectedFiles]);
  };

  const handleUpload = () => {
    if (!category) {
      alert("Please select upload category");
      return;
    }

    if (files.length === 0) {
      alert("Please upload at least 1 file!");
      return;
    }

    localStorage.setItem(
      "uploadedFiles",
      JSON.stringify(files.map((f) => f.name))
    );
    localStorage.setItem("uploadCategory", category);

    window.location.hash = "#/loading";
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2>Upload Files</h2>

        {/* Select category */}
        <label>Select Upload Type</label>
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">-- Select Upload Category --</option>
          <option value="Medical Report">Medical Report (PDF/Image)</option>
          <option value="Prescription">Prescription</option>
          <option value="Lab Report">Lab Report</option>
          <option value="Scan">Scan / MRI / X-Ray</option>
        </select>

        {/* File input */}
        <label>Choose Multiple Files</label>
        <input type="file" multiple onChange={handleFiles} />

        {/* Show file list */}
        {files.length > 0 && (
          <div className="file-list">
            <h4>Files Selected ({files.length}):</h4>
            <ul>
              {files.map((file, i) => (
                <li key={i}>• {file.name}</li>
              ))}
            </ul>
          </div>
        )}

        <button className="upload-btn" onClick={handleUpload}>
          Upload & Analyze
        </button>
      </div>
    </div>
  );
};

export default Upload;
