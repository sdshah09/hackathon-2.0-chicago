import React, { useEffect } from "react";
import "../styles/loading.css";

const Loading = () => {
  useEffect(() => {
    setTimeout(() => {
      window.location.hash = "#/result";
    }, 2500);
  }, []);

  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>Analyzing your files...</p>
    </div>
  );
};

export default Loading;
