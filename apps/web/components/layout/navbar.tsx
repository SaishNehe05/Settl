"use client";

import Link from "next/link";
import { ShieldCheck, Zap, Activity } from "lucide-react";
import { useAuth } from "@/components/auth/auth-provider";

export default function Navbar() {
  const { merchant } = useAuth();
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-800 bg-slate-950/80 px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-600 via-indigo-600 to-emerald-500 shadow-lg shadow-sky-500/20">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-white">Settl</span>
            <span className="ml-1.5 rounded bg-sky-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-sky-400 border border-sky-500/20">
              AI RECOVERY
            </span>
          </div>
        </Link>
      </div>

      <div className="flex items-center gap-4">
        {/* Razorpay Test Mode Badge */}
        <div className="flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-950/40 px-3 py-1 text-xs text-emerald-400 shadow-inner">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
          </span>
          <span className="font-medium">Razorpay Test Mode Active</span>
        </div>

        {/* Policy Guardrails Status */}
        <div className="hidden sm:flex items-center gap-1.5 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs text-slate-300">
          <ShieldCheck className="h-3.5 w-3.5 text-sky-400" />
          <span>Guardrails Enforced</span>
        </div>

        {/* Merchant Indicator */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-800">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-xs font-semibold text-white">
            {merchant?.name?.substring(0, 2).toUpperCase() || "SM"}
          </div>
          <div className="hidden md:block text-left text-xs leading-tight">
            <div className="font-medium text-slate-200 truncate max-w-[120px]">{merchant?.name || "Settl Merchant"}</div>
            <div className="text-[11px] text-slate-400 truncate max-w-[120px]">{merchant?.email || "merchant@settl.ai"}</div>
            <div className="text-[10px] font-mono text-sky-400/80 truncate max-w-[120px]" title="Copy this ID for the Demo Store">
              {merchant?.id || "MER_..."}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
