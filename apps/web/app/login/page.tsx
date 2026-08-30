"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, Lock, Mail, ArrowRight, ShieldCheck } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@settl.ai");
  const [password, setPassword] = useState("settl123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        throw new Error("Invalid email or password");
      }

      const data = await res.json();
      if (typeof window !== "undefined") {
        localStorage.setItem("settl_token", data.access_token);
        localStorage.setItem("settl_merchant_id", data.merchant_id);
      }
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Failed to sign in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-slate-900/60 p-8 rounded-2xl border border-slate-800 backdrop-blur-md shadow-2xl">
        <div className="text-center">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-sky-600 via-indigo-600 to-emerald-500 shadow-lg shadow-sky-500/20 mb-4">
            <Zap className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Sign in to Settl</h2>
          <p className="mt-1.5 text-xs text-slate-400">
            Autonomous AI Revenue Recovery Merchant Portal
          </p>
        </div>

        {error && (
          <div className="rounded-lg bg-rose-950/50 border border-rose-800/80 p-3 text-xs text-rose-300">
            {error}
          </div>
        )}

        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 pl-10 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                placeholder="merchant@example.com"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 pl-10 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-sky-600 py-2.5 text-xs font-semibold text-white hover:bg-sky-500 transition-colors shadow-lg shadow-sky-600/20 disabled:opacity-50"
          >
            {loading ? "Authenticating..." : "Sign in to Dashboard"}
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </form>

        <div className="pt-4 border-t border-slate-800 text-center">
          <div className="flex items-center justify-center gap-1.5 text-slate-500 text-[11px]">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            <span>Default demo credentials prefilled for testing</span>
          </div>
        </div>
      </div>
    </div>
  );
}
