"use client";

import { useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";

export default function ModeToggle() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mode = searchParams.get("mode") || "";
  const [isPending, startTransition] = useTransition();

  const handleModeChange = (newMode: string) => {
    if (mode === newMode) return;
    
    startTransition(() => {
      if (!newMode) {
        router.push("/");
      } else {
        router.push(`/?mode=${newMode}`);
      }
    });
  };

  return (
    <div className="flex items-center rounded-lg border border-slate-800 bg-slate-900/50 p-1 relative">
      <button
        onClick={() => handleModeChange("")}
        disabled={isPending}
        className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1.5 ${!mode ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'} ${isPending ? 'opacity-70 cursor-not-allowed' : ''}`}
      >
        {isPending && !mode && <Loader2 className="h-3 w-3 animate-spin" />}
        All Data
      </button>
      
      <button
        onClick={() => handleModeChange("simulation")}
        disabled={isPending}
        className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1.5 ${mode === 'simulation' ? 'bg-slate-800 text-purple-400 shadow-sm' : 'text-slate-400 hover:text-slate-200'} ${isPending ? 'opacity-70 cursor-not-allowed' : ''}`}
      >
        {isPending && mode === 'simulation' && <Loader2 className="h-3 w-3 animate-spin" />}
        Simulation
      </button>
      
      <button
        onClick={() => handleModeChange("api")}
        disabled={isPending}
        className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors flex items-center gap-1.5 ${mode === 'api' ? 'bg-slate-800 text-sky-400 shadow-sm' : 'text-slate-400 hover:text-slate-200'} ${isPending ? 'opacity-70 cursor-not-allowed' : ''}`}
      >
        {isPending && mode === 'api' && <Loader2 className="h-3 w-3 animate-spin" />}
        Razorpay
      </button>
    </div>
  );
}
