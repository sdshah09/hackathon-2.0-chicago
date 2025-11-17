import React, { useState } from 'react';

export default function Dropzone({ onFileSelect }) {
  const [dragging, setDragging] = useState(false);

  function handleDrag(e){
    e.preventDefault();
    setDragging(true);
  }

  function handleDrop(e){
    e.preventDefault();
    setDragging(false);
    if(e.dataTransfer.files.length > 0){
      onFileSelect(e.dataTransfer.files[0]);
    }
  }

  return (
    <div
      onDragOver={handleDrag}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      style={{
        border: "2px dashed #666",
        padding: "40px",
        textAlign: "center",
        borderRadius: "10px",
        background: dragging ? "#eef" : "#fafafa",
        cursor: "pointer"
      }}
    >
      <p style={{ fontSize: "18px" }}>Drag & Drop file here</p>
      <input
        type="file"
        onChange={(e)=>onFileSelect(e.target.files[0])}
        style={{ display: "none" }}
      />
    </div>
  );
}
