"use client";

import { createContext, useContext, useEffect, useState, useCallback, useRef, useSyncExternalStore, ReactNode } from "react";
import { api, setToken } from "@/lib/api";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface AuthUser {
  id: number;
  email: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (token: string, user: AuthUser) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

const subscribeToNothing = () => () => {};
const readAuthedCookie = () => document.cookie.includes("sw_authed=1");
const unknownOnServer = () => null;

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [sessionRestored, setSessionRestored] = useState(false);
  const refreshStarted = useRef(false);

  // Bootstrap decides once from the first client read; login() later writing the cookie must not reopen it.
  const authedCookie = useSyncExternalStore(subscribeToNothing, readAuthedCookie, unknownOnServer);
  const [cookieAtBoot, setCookieAtBoot] = useState<boolean | null>(null);
  if (cookieAtBoot === null && authedCookie !== null) {
    setCookieAtBoot(authedCookie);
  }
  const ready = cookieAtBoot === false || sessionRestored;

  useEffect(() => {
    if (cookieAtBoot !== true || refreshStarted.current) return;
    refreshStarted.current = true;

    let willRedirect = false;
    api.auth.refresh()
      .then(({ access_token }) => {
        setToken(access_token);
        return api.auth.me();
      })
      .then(setUser)
      .catch(() => {
        setToken(null);
        document.cookie = "sw_authed=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        willRedirect = true;
        window.location.href = "/login";
      })
      .finally(() => {
        if (!willRedirect) setSessionRestored(true);
      });
  }, [cookieAtBoot]);

  const login = useCallback((tok: string, usr: AuthUser) => {
    setToken(tok);
    document.cookie = "sw_authed=1; path=/; SameSite=Lax";
    setUser(usr);
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch(`${BASE}/auth/logout`, { method: "POST", credentials: "include" });
    } catch {}
    setToken(null);
    document.cookie = "sw_authed=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    setUser(null);
    window.location.href = "/login";
  }, []);

  if (!ready) {
    return (
      <div className="h-[100dvh] bg-[#030303] flex items-center justify-center">
        <div className="w-5 h-5 border-2 border-indigo-500/30 border-t-indigo-400 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
