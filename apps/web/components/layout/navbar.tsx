"use client";

import Link from "next/link";
import { ShieldCheck, Zap, User } from "lucide-react";
import { useAuth } from "@/components/auth/auth-provider";

export default function Navbar() {
  const { merchant } = useAuth();
  
  return (
    <header className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-800/60 bg-slate-950/80 px-6 backdrop-blur-xl">
      {/* LEFT: Branding */}
      <div className="flex items-center gap-3">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-sky-500/10 border border-sky-500/20 group-hover:border-sky-500/40 transition-colors">
            <Zap className="h-4 w-4 text-sky-400" />
          </div>
          <div className="flex flex-col">
            <span className="text-base font-bold tracking-tight text-slate-100 leading-tight">SETTL</span>
            <span className="text-[10px] font-medium text-slate-400 tracking-wider uppercase leading-none">AI Revenue Recovery</span>
          </div>
        </Link>
      </div>

      {/* RIGHT: Status & Account */}
      <div className="flex items-center gap-5">
        {/* Razorpay Test Mode Badge */}
        <div className="hidden sm:flex items-center gap-2 rounded border border-emerald-900/50 bg-emerald-950/30 px-2.5 py-1 text-xs text-emerald-400">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
          </span>
          <span className="font-medium tracking-wide">Razorpay Test Mode</span>
        </div>

        {/* Policy Guardrails Status */}
        <div className="hidden md:flex items-center gap-1.5 rounded border border-slate-800 bg-slate-900/40 px-2.5 py-1 text-xs text-slate-300">
          <ShieldCheck className="h-3.5 w-3.5 text-sky-400" />
          <span className="font-medium">Guardrails Active</span>
        </div>

        {/* Divider */}
        <div className="h-6 w-px bg-slate-800" />

        {/* Merchant Indicator */}
        <div className="flex items-center gap-3 group cursor-default" title={`Merchant ID: ${merchant?.id}`}>
          <div className="flex flex-col items-end hidden sm:flex">
            <span className="text-sm font-medium text-slate-200 leading-tight">
              {merchant?.name || "Settl Merchant"}
            </span>
            <span className="text-xs text-slate-500 leading-tight">
              {merchant?.email || "merchant@settl.ai"}
            </span>
          </div>
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-slate-300 border border-slate-700">
            <User className="h-4 w-4" />
          </div>
        </div>
      </div>
    </header>
  );
}
