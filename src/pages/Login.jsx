import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Login(){
  const nav = useNavigate();
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');

  function handleLogin(){
    if(user && pass){
      nav('/upload');
    } else {
      alert('Enter both fields');
    }
  }

  return (
    <div style={{ maxWidth:"400px", margin:"auto", padding:"40px" }}>
      <h1>Login</h1>
      <input 
        placeholder="User ID"
        value={user}
        onChange={e=>setUser(e.target.value)}
        style={{ width:"100%", padding:"10px", marginBottom:"10px" }}
      />
      <input 
        type="password"
        placeholder="Password"
        value={pass}
        onChange={e=>setPass(e.target.value)}
        style={{ width:"100%", padding:"10px" }}
      />
      <button 
        onClick={handleLogin}
        style={{
          marginTop:"20px",
          width:"100%",
          padding:"12px",
          background:"#4a90e2",
          color:"#fff",
          border:"none",
          borderRadius:"6px"
        }}
      >
        Login
      </button>
    </div>
  );
}
