import { useEffect, useState } from "react";

import { useAuth } from "../auth/context";
import { api } from "../api/client";

export function Profile() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name);
      setDisplayName(user.display_name ?? "");
    }
  }, [user]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(false);
    await api.put("/users/me", { full_name: fullName, display_name: displayName });
    await refreshUser();
    setSaved(true);
  };

  if (!user) return null;

  return (
    <div className="container form-narrow">
      <h2>Your profile</h2>
      <form onSubmit={onSubmit}>
        <label>Email</label>
        <input value={user.email} disabled />
        <label htmlFor="full">Full name</label>
        <input id="full" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <label htmlFor="display">Display name</label>
        <input id="display" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
        {saved && <p className="notice">Profile saved.</p>}
        <div style={{ marginTop: 16 }}>
          <button type="submit">Save</button>
        </div>
      </form>
    </div>
  );
}
