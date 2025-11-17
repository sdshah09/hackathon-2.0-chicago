import React, { useState } from "react";
import "../styles/login.css";

const Login = () => {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = () => {
    if (!name.trim()) {
      alert("Enter your full name");
      return;
    }

    if (!password.trim()) {
      alert("Enter your password");
      return;
    }

    // Store login details
    localStorage.setItem("fullName", name);
    localStorage.setItem("userPassword", password);

    window.location.hash = "#/dashboard";
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Login</h2>

        <label>Full Name</label>
        <input
          type="text"
          placeholder="Enter full name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <label>Password</label>
        <input
          type="password"
          placeholder="Enter password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button onClick={handleLogin}>Login</button>
      </div>
    </div>
  );
};

export default Login;
