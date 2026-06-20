import { useCallback, useEffect, useState } from "react";

import { api, type User } from "../api/client";
import { AuthContext, type AuthState } from "./context";

interface TokenResponse {
  access_token: string;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!localStorage.getItem("token")) {
      setUser(null);
      return;
    }
    try {
      setUser(await api.get<User>("/users/me"));
    } catch {
      localStorage.removeItem("token");
      setUser(null);
    }
  }, []);

  useEffect(() => {
    refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const { access_token } = await api.post<TokenResponse>("/auth/login", { email, password });
      localStorage.setItem("token", access_token);
      await refreshUser();
    },
    [refreshUser],
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      const { access_token } = await api.post<TokenResponse>("/auth/register", {
        email,
        password,
        full_name: fullName,
      });
      localStorage.setItem("token", access_token);
      await refreshUser();
    },
    [refreshUser],
  );

  const logout = useCallback(() => {
    void api.post("/auth/logout").catch(() => undefined);
    localStorage.removeItem("token");
    setUser(null);
  }, []);

  const value: AuthState = { user, loading, login, register, logout, refreshUser };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
