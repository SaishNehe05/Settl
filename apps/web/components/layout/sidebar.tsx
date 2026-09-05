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

  return (
    <aside className="w-[240px] border-r border-slate-200 bg-white flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-8">
        <div>
          <div className="px-3 mb-2 text-[10px] font-bold tracking-[0.2em] text-slate-400 uppercase">
            Workspace
          </div>
          <nav className="space-y-0.5">
            {[
              { href: "/", label: "Overview", icon: LayoutDashboard },
              { href: "/cases", label: "Recovery Queue", icon: Layers },
              { href: "/policies", label: "Policies", icon: ShieldAlert },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700 relative before:absolute before:inset-y-1 before:left-0 before:w-1 before:rounded-r before:bg-indigo-600"
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"
                  }`}
                >
                  <Icon className={`h-4 w-4 transition-colors ${isActive ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-500"}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div>
          <div className="px-3 mb-2 text-[10px] font-bold tracking-[0.2em] text-slate-400 uppercase">
            Insights
          </div>
          <nav className="space-y-0.5">
            {[
              { href: "/evaluation", label: "Recovery Intelligence", icon: BarChart3 },
            ].map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                    isActive
                      ? "bg-indigo-50 text-indigo-700 relative before:absolute before:inset-y-1 before:left-0 before:w-1 before:rounded-r before:bg-indigo-600"
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"
                  }`}
                >
                  <Icon className={`h-4 w-4 transition-colors ${isActive ? "text-indigo-600" : "text-slate-400 group-hover:text-slate-500"}`} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="space-y-1 pt-4 border-t border-slate-200">
        <button
          onClick={logout}
          className="group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-500 hover:bg-rose-50 hover:text-rose-600 transition-colors"
        >
          <LogOut className="h-4 w-4 text-slate-400 group-hover:text-rose-500 transition-colors" />
          Sign Out
        </button>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="group flex items-center justify-between rounded-lg px-3 py-2 text-xs font-medium text-slate-400 hover:bg-slate-50 hover:text-slate-600 transition-colors"
        >
          <span className="flex items-center gap-2">
            <FileCode2 className="h-4 w-4 text-slate-400 group-hover:text-slate-500 transition-colors" />
            API Docs
          </span>
        </a>
      </div>
    </aside>
  );
}
