"use client";

import { useState, FormEvent } from "react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";

type Tab = "login" | "register";

export default function LoginPage() {
  const { login } = useAuth();
  const [tab, setTab] = useState<Tab>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res =
        tab === "login"
          ? await api.auth.login(email, password)
          : await api.auth.register(email, password);
      const user = await api.auth.me();
      login(res.access_token, user);
      window.location.href = "/applications";
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      setError(msg.replace(/^API error \d+: /, ""));
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogle() {
    try {
      const { url } = await api.auth.googleUrl();
      window.location.href = url;
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : "Could not initiate Google sign-in";
      setError(msg.replace(/^API error \d+: /, ""));
    }
  }

  return (
    <main className="h-[100dvh] overflow-hidden flex items-center justify-center px-3 sm:px-4">
      <div className="w-full max-w-xs sm:max-w-sm">
        {/* Logo */}
        <div className="text-center mb-4 sm:mb-5">
          <span className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-indigo-400 to-rose-400 bg-clip-text text-transparent">
            SearchWork
          </span>
          <p className="mt-1 text-xs text-white/40">
            Your UK graduate job tracker
          </p>
        </div>

        {/* Card */}
        <div className="bg-white/[0.04] border border-white/[0.08] backdrop-blur-sm rounded-xl sm:rounded-2xl p-4 sm:p-6">
          {/* Tabs */}
          <div
            role="tablist"
            className="flex gap-1 mb-3 sm:mb-4 bg-white/[0.04] rounded-lg p-1"
          >
            {(["login", "register"] as Tab[]).map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                onClick={() => {
                  setTab(t);
                  setError(null);
                }}
                className={`flex-1 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-all duration-200 ${
                  tab === t
                    ? "bg-white/[0.1] text-white shadow-sm"
                    : "text-white/40 hover:text-white/70"
                }`}
              >
                {t === "login" ? "Sign in" : "Register"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-2.5 sm:space-y-3">
            <div className="space-y-1">
              <label className="text-[10px] sm:text-xs text-white/40 uppercase tracking-widest">
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                aria-describedby={error ? "form-error" : undefined}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-xs sm:text-sm text-white placeholder-white/20 outline-none focus:border-indigo-500/60 focus:bg-white/[0.06] transition-all"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] sm:text-xs text-white/40 uppercase tracking-widest">
                Password
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={
                  tab === "register" ? "Min. 8 characters" : "••••••••"
                }
                aria-describedby={error ? "form-error" : undefined}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-xs sm:text-sm text-white placeholder-white/20 outline-none focus:border-indigo-500/60 focus:bg-white/[0.06] transition-all"
              />
            </div>

            {error && (
              <p
                id="form-error"
                role="alert"
                className="text-rose-400 text-xs bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-1.5"
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 rounded-lg transition-colors text-xs sm:text-sm"
            >
              {loading
                ? "Please wait…"
                : tab === "login"
                  ? "Sign in"
                  : "Create account"}
            </button>
          </form>

          <div className="flex items-center gap-3 my-3">
            <div className="flex-1 h-px bg-white/[0.08]" />
            <span className="text-xs text-white/30">or</span>
            <div className="flex-1 h-px bg-white/[0.08]" />
          </div>

          <button
            onClick={handleGoogle}
            className="w-full flex items-center justify-center gap-2 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-white/80 hover:text-white font-medium py-2 rounded-lg transition-all text-xs sm:text-sm"
          >
            <GoogleIcon />
            Continue with Google
          </button>
        </div>
      </div>
    </main>
  );
}

function GoogleIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 18 18"
      fill="none"
      className="sm:w-[18px] sm:h-[18px]"
    >
      <path
        d="M17.64 9.205c0-.639-.057-1.252-.164-1.841H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z"
        fill="#4285F4"
      />
      <path
        d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z"
        fill="#34A853"
      />
      <path
        d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332Z"
        fill="#FBBC05"
      />
      <path
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58Z"
        fill="#EA4335"
      />
    </svg>
  );
}
