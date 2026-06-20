import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/context";

export function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await register(email, password, fullName);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Registration failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container form-narrow">
      <h2>Create an account</h2>
      <form onSubmit={onSubmit}>
        <label htmlFor="name">Full name</label>
        <input id="name" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <label htmlFor="email">Email</label>
        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <label htmlFor="password">Password (min 8 chars)</label>
        <input id="password" type="password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="error">{error}</p>}
        <div className="row" style={{ marginTop: 16 }}>
          <button type="submit" disabled={busy}>{busy ? "…" : "Register"}</button>
          <span className="muted">Have an account? <Link to="/login">Log in</Link></span>
        </div>
      </form>
    </div>
  );
}
