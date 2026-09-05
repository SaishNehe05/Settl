import { ShieldCheck, Sliders, AlertTriangle, CheckCircle2, ChevronRight, Activity, Zap, Ban, Server } from "lucide-react";
import { fetchPolicy } from "@/lib/api";
import { formatINR } from "@/lib/utils";

export const revalidate = 0;

export default async function PoliciesPage() {
  const policy = await fetchPolicy();

  return (
    <div className="space-y-8 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5 mb-2">
          <ShieldCheck className="h-6 w-6 text-emerald-600" />
          Safety Center & Guardrails
        </h1>
        <p className="text-sm text-slate-500 max-w-3xl leading-relaxed">
          The autonomous execution engine is strictly governed by a deterministic, code-level policy layer. 
          While AI is used for intent classification and probability estimation, <strong className="text-emerald-600 font-medium">all recovery actions</strong> must pass these hardcoded constraints before executing.
        </p>
      </div>

      {/* Principle Callout */}
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800 leading-relaxed flex items-start gap-4">
        <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-700">Immutable Deterministic Policy Invariant:</span>
          {" "}The LLM recommends actions, but <strong>never</strong> directly manipulates production databases, invokes external payment gateways, or bypasses these policies. 
          LLM outputs map to finite enums (e.g., <code>CREATE_PAYMENT_LINK</code>), which are evaluated by the deterministic engine below.
        </div>
      </div>

      {/* Visual Diagram of Flow */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 overflow-hidden relative">
         <h2 className="text-sm font-semibold mb-6 flex items-center gap-2 uppercase tracking-wider text-slate-500">
           <Activity className="h-4 w-4 text-emerald-500" />
           Execution Safety Architecture
         </h2>
         
         <div className="flex flex-col md:flex-row justify-between items-stretch gap-3 text-center relative z-10">
           {/* Step 1: LLM */}
           <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg p-5 flex flex-col items-center justify-center relative hover:bg-slate-100 transition-colors">
             <Zap className="h-6 w-6 text-indigo-500 mb-3" />
             <div className="text-xs font-semibold text-slate-700 uppercase tracking-wider">1. Agent Analysis</div>
             <div className="text-[11px] text-slate-500 mt-2">Determines Root Cause & Probability. Emits finite Action Enum.</div>
             <div className="hidden md:block absolute -right-3.5 top-1/2 -translate-y-1/2 text-slate-300 z-20">
               <ChevronRight className="h-5 w-5" />
             </div>
           </div>
           
           {/* Step 2: Policy Engine */}
           <div className="flex-1 bg-emerald-50 border border-emerald-200 rounded-lg p-5 flex flex-col items-center justify-center relative hover:bg-emerald-100 transition-colors">
             <ShieldCheck className="h-6 w-6 text-emerald-600 mb-3" />
             <div className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">2. Deterministic Gate</div>
             <div className="text-[11px] text-emerald-600/70 mt-2">Evaluates against strict financial and rate limits (below).</div>
             <div className="hidden md:block absolute -right-3.5 top-1/2 -translate-y-1/2 text-emerald-300 z-20">
               <ChevronRight className="h-5 w-5" />
             </div>
           </div>

           {/* Step 3: Execution */}
           <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg p-5 flex flex-col items-center justify-center relative hover:bg-slate-100 transition-colors">
             <Server className="h-6 w-6 text-violet-500 mb-3" />
             <div className="text-xs font-semibold text-slate-700 uppercase tracking-wider">3. Action Execution</div>
             <div className="text-[11px] text-slate-500 mt-2">Calls external APIs (Razorpay) and updates system state.</div>
           </div>
         </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Rules Config Cards */}
        <div className="space-y-4">
          <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider text-slate-500">
            Active Constraints
          </h2>

          <div className="rounded-xl border border-slate-200 bg-white p-5 flex flex-col gap-3 group hover:border-slate-300 hover:shadow-sm transition-all">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-900">Maximum Automated Attempts</div>
              <span className="font-mono text-lg font-bold text-indigo-600">
                {policy.max_attempts}
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Limits how many recovery notifications or payment links can be issued per case before automation permanently halts. Prevents customer fatigue.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 flex flex-col gap-3 group hover:border-slate-300 hover:shadow-sm transition-all">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-900">Maximum Automated Amount</div>
              <span className="font-mono text-lg font-bold text-indigo-600">
                {formatINR(policy.max_automated_amount_paise)}
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Cases above this value bypass automation entirely and are routed directly to the Human Operator review queue for manual intervention.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 flex flex-col gap-3 group hover:border-slate-300 hover:shadow-sm transition-all">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-900">Minimum Recovery Probability</div>
              <span className="font-mono text-lg font-bold text-indigo-600">
                {(policy.min_probability * 100).toFixed(0)}%
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Low-probability cases below this threshold are blocked by the policy engine to protect customer goodwill and reduce unnecessary outreach.
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 flex flex-col gap-3 group hover:border-slate-300 hover:shadow-sm transition-all">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-slate-900">Cooldown Duration</div>
              <span className="font-mono text-lg font-bold text-indigo-600">
                {policy.cooldown_minutes} min
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Minimum delay enforced between consecutive recovery follow-up attempts to prevent system spamming and ensure compliance.
            </p>
          </div>
        </div>

        {/* Active Enforcement Matrix */}
        <div>
          <h2 className="text-sm font-semibold mb-4 uppercase tracking-wider text-slate-500">
            Enforcement Logic Matrix
          </h2>
          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
            <div className="divide-y divide-slate-100 text-xs">
              <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-2">
                  <Ban className="h-4 w-4 text-rose-500 shrink-0" />
                  <span className="text-slate-600 font-medium">Attempt Count &ge; {policy.max_attempts}</span>
                </div>
                <span className="inline-flex items-center rounded-md bg-rose-50 px-2 py-1 font-mono text-[10px] font-bold text-rose-600 ring-1 ring-inset ring-rose-200">
                  BLOCK &rarr; STOP
                </span>
              </div>
              <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-2">
                  <Ban className="h-4 w-4 text-purple-500 shrink-0" />
                  <span className="text-slate-600 font-medium">Amount &gt; {formatINR(policy.max_automated_amount_paise)}</span>
                </div>
                <span className="inline-flex items-center rounded-md bg-purple-50 px-2 py-1 font-mono text-[10px] font-bold text-purple-600 ring-1 ring-inset ring-purple-200">
                  BLOCK &rarr; ESCALATE
                </span>
              </div>
              <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-2">
                  <Ban className="h-4 w-4 text-rose-500 shrink-0" />
                  <span className="text-slate-600 font-medium">Probability &lt; {(policy.min_probability * 100).toFixed(0)}%</span>
                </div>
                <span className="inline-flex items-center rounded-md bg-rose-50 px-2 py-1 font-mono text-[10px] font-bold text-rose-600 ring-1 ring-inset ring-rose-200">
                  BLOCK &rarr; STOP
                </span>
              </div>
              <div className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-2">
                  <Ban className="h-4 w-4 text-rose-500 shrink-0" />
                  <span className="text-slate-600 font-medium">Customer Comm Opt-Out = True</span>
                </div>
                <span className="inline-flex items-center rounded-md bg-rose-50 px-2 py-1 font-mono text-[10px] font-bold text-rose-600 ring-1 ring-inset ring-rose-200">
                  BLOCK &rarr; STOP
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
