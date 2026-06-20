import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/context";

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container form-narrow">
      <h2>Log in</h2>
      <form onSubmit={onSubmit}>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <label htmlFor="password">Password</label>
        <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="error">{error}</p>}
        <div className="row" style={{ marginTop: 16 }}>
          <button type="submit" disabled={busy}>{busy ? "…" : "Log in"}</button>
          <span className="muted">No account? <Link to="/register">Register</Link></span>
        </div>
      </form>
    </div>
  );
}
