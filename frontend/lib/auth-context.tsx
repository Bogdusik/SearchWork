"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";

const TOKEN_KEY = "sw_access_token";

interface AuthUser {
  id: number;
  email: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: AuthUser) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      setToken(stored);
      fetchMe(stored).then(setUser).catch(() => clearState());
    }
  }, []);

  const login = useCallback((tok: string, usr: AuthUser) => {
    localStorage.setItem(TOKEN_KEY, tok);
    document.cookie = "sw_authed=1; path=/; SameSite=Lax";
    setToken(tok);
    setUser(usr);
  }, []);

  const logout = useCallback(async () => {
    const tok = localStorage.getItem(TOKEN_KEY);
    if (tok) {
      try {
        await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/auth/logout`, {
          method: "POST",
          headers: { Authorization: `Bearer ${tok}` },
          credentials: "include",
        });
      } catch {}
    }
    clearState();
    window.location.href = "/login";
  }, []);

  function clearState() {
    localStorage.removeItem(TOKEN_KEY);
    document.cookie = "sw_authed=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

async function fetchMe(tok: string): Promise<AuthUser> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/auth/me`, {
    headers: { Authorization: `Bearer ${tok}` },
  });
  if (!res.ok) throw new Error("unauthorized");
  return res.json();
}
