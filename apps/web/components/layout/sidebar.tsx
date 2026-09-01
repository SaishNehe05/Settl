"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Layers, 
  ShieldAlert, 
  BarChart3, 
  FileCode2,
  HelpCircle,
  LogOut 
} from "lucide-react";
import { useAuth } from "@/components/auth/auth-provider";

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, merchant } = useAuth();

  const links = [
    { href: "/", label: "Overview", icon: LayoutDashboard },
    { href: "/cases", label: "Recovery Queue", icon: Layers },
    { href: "/policies", label: "Guardrails & Policy", icon: ShieldAlert },
    { href: "/evaluation", label: "Batch Evaluation", icon: BarChart3 },
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950 flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div>
          <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
            Platform
          </div>
          <nav className="space-y-1">
            {links.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                    isActive
                      ? "bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-sm"
                      : "text-slate-400 hover:bg-slate-900/60 hover:text-slate-200"
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? "text-sky-400" : "text-slate-400"}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Core Principle Callout */}
        <div className="rounded-xl border border-slate-800 bg-gradient-to-b from-slate-900/80 to-slate-950 p-3.5 text-xs text-slate-400">
          <div className="flex items-center gap-1.5 font-semibold text-slate-200 mb-1.5">
            <span>Operational Invariant</span>
          </div>
          <p className="text-[11px] leading-relaxed text-slate-400">
            <strong className="text-sky-400">LLM recommends</strong>, deterministic policy code authorizes, Razorpay executes, verified webhooks confirm recovery.
          </p>
        </div>
      </div>

      <div className="space-y-2 pt-4 border-t border-slate-800/60">
        {/* Merchant Info & Logout */}
        <div className="mb-4">
          <div className="mb-3 px-2">
            <p className="text-xs font-medium text-slate-300 truncate">
              {merchant?.name || "Acme Retail India"}
            </p>
            <p className="text-[10px] text-slate-500 truncate">
              {merchant?.email || "admin@acme.in"}
            </p>
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-400 hover:bg-rose-500/10 hover:text-rose-400 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-colors"
        >
          <span className="flex items-center gap-2">
            <FileCode2 className="h-3.5 w-3.5 text-slate-400" />
            FastAPI Swagger
          </span>
          <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">:8000</span>
        </a>
      </div>
    </aside>
  );
}
