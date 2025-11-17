import React, { useState } from "react";
import "../styles/upload.css";

const Upload = () => {
  const [category, setCategory] = useState("");
  const [files, setFiles] = useState([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Backend API URL - adjust if needed
  const API_URL = "http://localhost:8000";

  const handleFiles = (e) => {
    const selectedFiles = Array.from(e.target.files);

    // Validate file types
    const allowedTypes = [
      "image/jpeg",
      "image/jpg",
      "image/png",
      "application/pdf",
    ];
    const invalidFiles = selectedFiles.filter(
      (file) => !allowedTypes.includes(file.type)
    );

    if (invalidFiles.length > 0) {
      alert(
        `Invalid file types detected. Only JPEG, PNG, and PDF files are allowed.\nInvalid files: ${invalidFiles
          .map((f) => f.name)
          .join(", ")}`
      );
      return;
    }

    // Check file sizes (50MB max)
    const maxSize = 50 * 1024 * 1024; // 50MB
    const oversizedFiles = selectedFiles.filter((file) => file.size > maxSize);

    if (oversizedFiles.length > 0) {
      alert(
        `Some files exceed the 50MB limit:\n${oversizedFiles
          .map((f) => `${f.name} (${(f.size / 1024 / 1024).toFixed(2)}MB)`)
          .join("\n")}`
      );
      return;
    }

    // Add uploaded files without removing the existing ones
    setFiles((prev) => [...prev, ...selectedFiles]);
  };

  const removeFile = (indexToRemove) => {
    setFiles((prev) => prev.filter((_, index) => index !== indexToRemove));
  };

  const handleUpload = async () => {
    setError("");

    // Validation
    if (!category) {
      setError("Please select upload category");
      return;
    }

    if (files.length === 0) {
      setError("Please upload at least 1 file!");
      return;
    }

    // Get username from localStorage (stored during login)
    const username = localStorage.getItem("username");
    if (!username) {
      setError("User not logged in. Please login first.");
      window.location.hash = "#/login";
      return;
    }

    setLoading(true);

    try {
      // Create FormData to send files
      const formData = new FormData();

      // Append all files to FormData
      files.forEach((file) => {
        formData.append("files", file);
      });

      // Make API request to upload files
      const response = await fetch(
        `${API_URL}/users/${username}/files/upload`,
        {
          method: "POST",
          body: formData,
          // Don't set Content-Type header - browser will set it automatically with boundary
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "File upload failed");
      }

      // Success! Store metadata and navigate
      localStorage.setItem("uploadedFiles", JSON.stringify(data.files));
      localStorage.setItem("uploadCategory", category);
      localStorage.setItem("uploadPrompt", prompt);
      localStorage.setItem("uploadMessage", data.message);

      // Navigate to loading page
      window.location.hash = "#/loading";
    } catch (err) {
      console.error("Upload error:", err);
      setError(err.message || "An error occurred during file upload");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2>Upload Files</h2>

        {error && <div className="error-message">{error}</div>}

        {/* Select category */}
        <label>Select Upload Type</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          disabled={loading}
        >
          <option value="">-- Select Upload Category --</option>
          <option value="Medical Report">Medical Report (PDF/Image)</option>
          <option value="Prescription">Prescription</option>
          <option value="Lab Report">Lab Report</option>
          <option value="Scan">Scan / MRI / X-Ray</option>
        </select>

        {/* File input */}
        <label>Choose Multiple Files (JPEG, PNG, PDF - Max 50MB each)</label>
        <input
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
          onChange={handleFiles}
          disabled={loading}
        />

        {/* Show file list */}
        {files.length > 0 && (
          <div className="file-list">
            <h4>Files Selected ({files.length}):</h4>
            <ul>
              {files.map((file, i) => (
                <li key={i}>
                  • {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  {!loading && (
                    <button
                      className="remove-file-btn"
                      onClick={() => removeFile(i)}
                      type="button"
                    >
                      ✕
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        <label>Insert a prompt to help analyze your documents (Optional)</label>
        <textarea
          name="prompt"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="E.g., Focus on blood pressure readings and medication history..."
          rows="4"
          disabled={loading}
        />

        <button
          className="upload-btn"
          onClick={handleUpload}
          disabled={loading}
        >
          {loading ? "Uploading..." : "Upload & Analyze"}
        </button>

        {loading && (
          <div className="upload-progress">
            <p>Uploading {files.length} file(s)... Please wait.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Upload;
