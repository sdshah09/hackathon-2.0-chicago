import React, { useState } from "react";
import "../styles/patientform.css";

const PatientForm = () => {
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("");
  const [symptoms, setSymptoms] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [specialist, setSpecialist] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();

    const data = { age, gender, symptoms, diagnosis, specialist };

    localStorage.setItem("patientInfo", JSON.stringify(data));

    window.location.hash = "#/upload";
  };

  return (
    <div className="form-container">
      <form className="form-card" onSubmit={handleSubmit}>
        <h2>Patient Details</h2>

        <label>Age</label>
        <input value={age} onChange={(e) => setAge(e.target.value)} />

        <label>Gender</label>
        <select value={gender} onChange={(e) => setGender(e.target.value)}>
          <option>Select</option>
          <option>Male</option>
          <option>Female</option>
          <option>Other</option>
        </select>

        <label>Symptoms</label>
        <textarea value={symptoms} onChange={(e) => setSymptoms(e.target.value)} />

        <label>Past Diagnosis</label>
        <textarea value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)} />

        <label>Specialist</label>
        <select value={specialist} onChange={(e) => setSpecialist(e.target.value)}>
          <option>Select Specialist</option>
          <option>Cardiologist</option>
          <option>Dermatologist</option>
          <option>Neurologist</option>
          <option>General Physician</option>
        </select>

        <button type="submit">Continue</button>
      </form>
    </div>
  );
};

export default PatientForm;
