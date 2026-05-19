"use client";

import { useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api, setToken } from "@/lib/api";

function CallbackInner() {
  const params = useSearchParams();
  const { login } = useAuth();

  useEffect(() => {
    const token = params.get("access_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }
    setToken(token);
    api.auth.me()
      .then((user) => {
        login(token, user);
        window.location.href = "/applications";
      })
      .catch(() => {
        setToken(null);
        window.location.href = "/login";
      });
  }, [params, login]);

  return (
    <main className="h-[100dvh] overflow-hidden flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-sm text-white/40">Signing you in…</p>
      </div>
    </main>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense>
      <CallbackInner />
    </Suspense>
  );
}
