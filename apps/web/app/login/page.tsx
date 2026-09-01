"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/auth-provider";
import { API_BASE } from "@/lib/api";
import { Zap, ArrowRight, UserPlus, LogIn } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const endpoint = isRegister ? "/api/v1/auth/register" : "/api/v1/auth/login";
      const body = isRegister
        ? JSON.stringify({ name, email, password })
        : JSON.stringify({ email, password });

      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `${isRegister ? "Registration" : "Login"} failed`);
      }

      const data = await res.json();
      
      // Set cookie for Server Components
      document.cookie = `settl_token=${data.access_token}; path=/; max-age=86400; SameSite=Lax`;
      
      login(data.access_token, {
        id: data.merchant_id,
        name: data.merchant_name,
        email,
      });

      router.push("/");
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8">
        {/* Logo */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2.5 mb-4">
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20">
              <Zap className="h-7 w-7 text-sky-400" />
            </div>
            <span className="text-2xl font-bold text-white tracking-tight">Settl</span>
          </div>
          <p className="text-sm text-slate-400">
            AI-Powered Revenue Recovery Agent
          </p>
        </div>

        {/* Auth Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-8 shadow-2xl backdrop-blur-sm">
          {/* Tab Switcher */}
          <div className="flex rounded-xl bg-slate-800/60 p-1 mb-6">
            <button
              onClick={() => { setIsRegister(false); setError(""); }}
              className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-semibold transition-all ${
                !isRegister
                  ? "bg-sky-600 text-white shadow-lg shadow-sky-600/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <LogIn className="h-3.5 w-3.5" />
              Sign In
            </button>
            <button
              onClick={() => { setIsRegister(true); setError(""); }}
              className={`flex-1 flex items-center justify-center gap-2 rounded-lg py-2.5 text-xs font-semibold transition-all ${
                isRegister
                  ? "bg-sky-600 text-white shadow-lg shadow-sky-600/20"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <UserPlus className="h-3.5 w-3.5" />
              Create Account
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                  Business Name
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your company or business name"
                  className="w-full rounded-lg border border-slate-700/80 bg-slate-800/60 px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none focus:border-sky-500/60 focus:ring-1 focus:ring-sky-500/30 transition-all"
                />
              </div>
            )}

            <div>
              <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full rounded-lg border border-slate-700/80 bg-slate-800/60 px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none focus:border-sky-500/60 focus:ring-1 focus:ring-sky-500/30 transition-all"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-slate-700/80 bg-slate-800/60 px-4 py-2.5 text-sm text-slate-200 placeholder:text-slate-500 outline-none focus:border-sky-500/60 focus:ring-1 focus:ring-sky-500/30 transition-all"
              />
            </div>

            {error && (
              <div className="rounded-lg border border-red-500/30 bg-red-950/40 px-4 py-2.5 text-xs text-red-400">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-sky-600 py-3 text-sm font-semibold text-white hover:bg-sky-500 transition-colors shadow-lg shadow-sky-600/20 disabled:opacity-50"
            >
              {loading ? (
                "Processing..."
              ) : (
                <>
                  {isRegister ? "Create Account" : "Sign In"}
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-slate-600">
          Settl creates a secure merchant account with isolated data.
        </p>
      </div>
    </div>
  );
}
