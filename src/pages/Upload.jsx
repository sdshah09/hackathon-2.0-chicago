import React, { useState } from 'react';
import Dropzone from '../components/Dropzone.jsx';
import { useNavigate } from 'react-router-dom';

export default function Upload(){
  const [file, setFile] = useState(null);
  const nav = useNavigate();

  function handleProcess(){
    nav('/result');
  }

  return (
    <div style={{ maxWidth:"600px", margin:"auto", padding:"40px" }}>
      <h1>Upload File</h1>

      <Dropzone onFileSelect={(f)=>setFile(f)} />

      {file && <p style={{ marginTop:"20px" }}>Selected: {file.name}</p>}

      <button
        onClick={handleProcess}
        style={{
          marginTop:"20px",
          width:"100%",
          padding:"12px",
          background:"#28a745",
          color:"#fff",
          border:"none",
          borderRadius:"6px"
        }}
      >
        Continue
      </button>
    </div>
  );
}
