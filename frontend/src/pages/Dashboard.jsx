import React from "react";
import "../styles/dashboard.css";

const Dashboard = () => {
  const name = localStorage.getItem("user") || "User";

  return (
    <div className="dash-container">
      <div className="dash-card">
        <h1>Hello {name} 👋</h1>
        <p>Welcome to AI Medical Summary System</p>

        <button onClick={() => window.location.hash = "#/upload"}>
          Upload Medical Files
        </button>
      </div>
    </div>
  );
};

export default Dashboard;
