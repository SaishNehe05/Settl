import { ShieldCheck, Sliders, AlertTriangle, CheckCircle2 } from "lucide-react";
import { fetchPolicy } from "@/lib/api";
import { formatINR } from "@/lib/utils";

export const revalidate = 0;

export default async function PoliciesPage() {
  const policy = await fetchPolicy();

  return (
    <div className="space-y-8 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
          <ShieldCheck className="h-6 w-6 text-sky-400" />
          Merchant Recovery Guardrails
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Deterministic safety rules that strictly govern which recovery actions the AI agent is allowed to execute.
        </p>
      </div>

      {/* Principle Callout */}
      <div className="rounded-xl border border-amber-500/20 bg-amber-950/20 p-4 text-xs text-amber-200/90 leading-relaxed flex items-start gap-3">
        <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-300">Deterministic Policy Invariant:</span>
          {" "}The LLM recommends recovery actions, but never directly charges customers or bypasses policies. All external payment link creation is authorized solely through deterministic code rules.
        </div>
      </div>

      {/* Rules Config Cards */}
      <div className="space-y-4">
        {/* Rule 1: Max Automated Attempts */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 flex items-center justify-between">
          <div className="space-y-1">
            <div className="text-sm font-semibold text-white">Maximum Automated Attempts</div>
            <p className="text-xs text-slate-400">
              Limits how many recovery notifications or links can be issued per case before automation halts.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg font-bold text-sky-400 bg-slate-950 border border-slate-800 px-3 py-1 rounded-lg">
              {policy.max_attempts}
            </span>
            <span className="text-xs text-slate-500">attempts</span>
          </div>
        </div>

        {/* Rule 2: Max Automated Amount */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 flex items-center justify-between">
          <div className="space-y-1">
            <div className="text-sm font-semibold text-white">Maximum Automated Amount</div>
            <p className="text-xs text-slate-400">
              Cases above this value are automatically routed to the Human Operator review queue.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg font-bold text-sky-400 bg-slate-950 border border-slate-800 px-3 py-1 rounded-lg">
              {formatINR(policy.max_automated_amount_paise)}
            </span>
          </div>
        </div>

        {/* Rule 3: Minimum Recovery Probability */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 flex items-center justify-between">
          <div className="space-y-1">
            <div className="text-sm font-semibold text-white">Minimum Recovery Probability</div>
            <p className="text-xs text-slate-400">
              Low-probability cases below this threshold are marked STOP to protect customer goodwill.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg font-bold text-sky-400 bg-slate-950 border border-slate-800 px-3 py-1 rounded-lg">
              {(policy.min_probability * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        {/* Rule 4: Cooldown Window */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 flex items-center justify-between">
          <div className="space-y-1">
            <div className="text-sm font-semibold text-white">Cooldown Duration</div>
            <p className="text-xs text-slate-400">
              Minimum delay between consecutive recovery follow-up attempts to prevent spamming.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg font-bold text-sky-400 bg-slate-950 border border-slate-800 px-3 py-1 rounded-lg">
              {policy.cooldown_minutes}
            </span>
            <span className="text-xs text-slate-500">minutes</span>
          </div>
        </div>
      </div>

      {/* Active Enforcement Matrix */}
      <div className="rounded-xl border border-slate-800 bg-slate-950 p-5 space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Enforcement Logic Matrix
        </h3>
        <div className="divide-y divide-slate-800/80 text-xs">
          <div className="py-2.5 flex items-center justify-between">
            <span className="text-slate-300">Attempt Count &ge; {policy.max_attempts}</span>
            <span className="font-mono text-rose-400 font-semibold">BLOCK &rarr; STOP</span>
          </div>
          <div className="py-2.5 flex items-center justify-between">
            <span className="text-slate-300">Amount &gt; {formatINR(policy.max_automated_amount_paise)}</span>
            <span className="font-mono text-purple-400 font-semibold">BLOCK &rarr; ESCALATE</span>
          </div>
          <div className="py-2.5 flex items-center justify-between">
            <span className="text-slate-300">Probability &lt; {(policy.min_probability * 100).toFixed(0)}%</span>
            <span className="font-mono text-rose-400 font-semibold">BLOCK &rarr; STOP</span>
          </div>
          <div className="py-2.5 flex items-center justify-between">
            <span className="text-slate-300">Customer Communication Opt-Out = True</span>
            <span className="font-mono text-rose-400 font-semibold">BLOCK &rarr; STOP</span>
          </div>
        </div>
      </div>
    </div>
  );
}
