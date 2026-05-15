"use client";

import { useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";

function CallbackInner() {
  const params = useSearchParams();
  const router = useRouter();
  const { login } = useAuth();

  useEffect(() => {
    const token = params.get("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }
    localStorage.setItem("sw_access_token", token);
    document.cookie = "sw_authed=1; path=/; SameSite=Lax";
    api.auth.me()
      .then((user) => {
        login(token, user);
        router.replace("/applications");
      })
      .catch(() => {
        localStorage.removeItem("sw_access_token");
        document.cookie = "sw_authed=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
        router.replace("/login");
      });
  }, [params, router, login]);

  return (
    <main className="min-h-screen flex items-center justify-center">
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
