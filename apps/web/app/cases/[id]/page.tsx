import Link from "next/link";
import { notFound } from "next/navigation";
import { 
  ArrowLeft, 
  CheckCircle2, 
  Clock, 
  ExternalLink, 
  FileText, 
  Layers, 
  Lock, 
  ShieldCheck, 
  UserCheck, 
  Zap 
} from "lucide-react";
import { fetchCaseDetail } from "@/lib/api";
import { formatINR, formatPercent, formatDate } from "@/lib/utils";
import StatusBadge from "@/components/cases/status-badge";
import CaseActions from "@/components/cases/case-actions";

interface CaseDetailPageProps {
  params: Promise<{ id: string }>;
}

export const revalidate = 0;

export default async function CaseDetailPage({ params }: CaseDetailPageProps) {
  const { id } = await params;
  const caseDetail = await fetchCaseDetail(id);

  if (!caseDetail) {
    notFound();
  }

  // State machine sequence definition
  const stateSteps = [
    { label: "New Event", state: "NEW" },
    { label: "AI Analysis", state: "ANALYZING" },
    { label: "Case Ready", state: "READY" },
    { label: "Policy Gate", state: "POLICY_CHECK" },
    { label: "Approved", state: "APPROVED" },
    { label: "Razorpay Exec", state: "EXECUTING" },
    { label: "Webhook Verify", state: "WAITING_RESULT" },
    { label: "Recovered", state: "RECOVERED" },
  ];

  const getStepStatus = (stepState: string) => {
    if (caseDetail.status === "RECOVERED") return "completed";
    if (caseDetail.status === "BLOCKED" || caseDetail.status === "STOPPED") {
      if (["NEW", "ANALYZING", "READY", "POLICY_CHECK"].includes(stepState)) return "completed";
      return "blocked";
    }
    if (caseDetail.status === "ESCALATED") {
      if (["NEW", "ANALYZING", "READY", "POLICY_CHECK"].includes(stepState)) return "completed";
      return "escalated";
    }
    if (stepState === caseDetail.status) return "current";
    return "pending";
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Navigation & Header */}
      <div>
        <Link
          href="/cases"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors mb-3"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Recovery Queue
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">{caseDetail.id}</h1>
            <StatusBadge status={caseDetail.status} />
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300 font-medium">
              {caseDetail.priority} Priority
            </span>
          </div>
          <div className="flex items-center gap-5">
            <CaseActions caseId={caseDetail.id} status={caseDetail.status} />
            <div className="text-right">
              <div className="text-xs text-slate-400">Amount at Risk</div>
              <div className="text-2xl font-bold text-white tracking-tight">
                {formatINR(caseDetail.amount_at_risk_paise)}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Visual State Machine Stepper */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
          <Layers className="h-4 w-4 text-sky-400" />
          State Machine Progression
        </h2>
        <div className="flex flex-wrap items-center gap-2">
          {stateSteps.map((step, idx) => {
            const stepStatus = getStepStatus(step.state);
            let pillClass = "bg-slate-950 border-slate-800 text-slate-500";
            if (stepStatus === "completed") {
              pillClass = "bg-emerald-950/60 border-emerald-800 text-emerald-300";
            } else if (stepStatus === "current") {
              pillClass = "bg-sky-950/80 border-sky-600 text-sky-300 ring-2 ring-sky-500/20";
            } else if (stepStatus === "blocked") {
              pillClass = "bg-rose-950/40 border-rose-900/60 text-rose-400";
            } else if (stepStatus === "escalated") {
              pillClass = "bg-purple-950/40 border-purple-900/60 text-purple-400";
            }

            return (
              <div key={idx} className="flex items-center gap-2">
                <div className={`rounded-lg border px-3 py-1.5 text-xs font-medium ${pillClass}`}>
                  <span className="opacity-60 text-[10px] mr-1">0{idx + 1}</span>
                  {step.label}
                </div>
                {idx < stateSteps.length - 1 && (
                  <span className="text-slate-600 text-xs hidden md:inline">→</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Grid: Case Details & Intelligence */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer Context */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <UserCheck className="h-4 w-4 text-indigo-400" />
            Customer Intelligence
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <div className="text-slate-500">Customer Name</div>
              <div className="font-semibold text-slate-200 text-sm mt-0.5">
                {caseDetail.customer?.name || caseDetail.customer_name || "Demo Customer"}
              </div>
            </div>
            <div>
              <div className="text-slate-500">Contact</div>
              <div className="text-slate-300 font-mono mt-0.5">
                {caseDetail.customer?.email || caseDetail.customer_email || "demo@example.com"}
              </div>
              <div className="text-slate-400 font-mono mt-0.5">
                {caseDetail.customer?.phone || "+91 98765 43210"}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800">
              <div>
                <div className="text-slate-500">Payment Success Rate</div>
                <div className="font-semibold text-emerald-400 text-sm mt-0.5">
                  {formatPercent(caseDetail.customer?.success_rate ?? 0.95)}
                </div>
              </div>
              <div>
                <div className="text-slate-500">Customer Tier</div>
                <div className="font-semibold text-purple-400 text-sm mt-0.5">
                  {caseDetail.customer?.customer_value || "HIGH"}
                </div>
              </div>
            </div>
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
              <span className="text-slate-500">Communication Opt-Out</span>
              <span className={`font-medium ${caseDetail.customer?.opted_out ? "text-rose-400" : "text-emerald-400"}`}>
                {caseDetail.customer?.opted_out ? "Opted Out" : "Consent Active"}
              </span>
            </div>
          </div>
        </div>

        {/* AI Root Cause & Recommendation */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
              <Zap className="h-4 w-4 text-sky-400" />
              AI Root Cause & Decision
            </div>
            {caseDetail.latest_prediction && (
              <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-mono text-emerald-400">
                {caseDetail.latest_prediction.validation_status || "VALID"}
              </span>
            )}
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <div className="text-slate-500">Estimated Recovery Probability</div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xl font-bold text-sky-400 font-mono">
                  {formatPercent(caseDetail.recovery_probability)}
                </span>
                <span className="text-[11px] text-slate-400">
                  (Calibrated Risk Model)
                </span>
              </div>
            </div>
            <div>
              <div className="text-slate-500">Diagnostic Root Cause</div>
              <div className="text-slate-200 mt-1 bg-slate-950 px-3 py-2 rounded-lg border border-slate-800 font-sans leading-relaxed">
                {caseDetail.root_cause || "Analyzing event..."}
              </div>
            </div>

            {/* Structured Evidence Tags */}
            {(() => {
              let aiMeta: any = null;
              try {
                if (caseDetail.latest_prediction?.reason) {
                  aiMeta = JSON.parse(caseDetail.latest_prediction.reason);
                }
              } catch {}

              if (aiMeta?.evidence && aiMeta.evidence.length > 0) {
                return (
                  <div>
                    <div className="text-slate-500 mb-1.5">Grounded Evidence</div>
                    <div className="flex flex-wrap gap-1.5">
                      {aiMeta.evidence.map((ev: string, i: number) => (
                        <span
                          key={i}
                          className="rounded bg-slate-800/80 border border-slate-700/60 px-2 py-0.5 text-[11px] text-slate-300"
                        >
                          {ev}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              }
              return null;
            })()}

            <div>
              <div className="text-slate-500">Decision Agent Recommendation</div>
              <div className="flex items-center justify-between font-mono font-semibold text-emerald-400 mt-1 bg-emerald-950/30 px-3 py-2 rounded-lg border border-emerald-800/50">
                <span>{caseDetail.recommended_action || "CREATE_PAYMENT_LINK"}</span>
                {(() => {
                  let aiMeta: any = null;
                  try {
                    if (caseDetail.latest_prediction?.reason) {
                      aiMeta = JSON.parse(caseDetail.latest_prediction.reason);
                    }
                  } catch {}
                  return aiMeta?.channel ? (
                    <span className="text-[10px] text-emerald-300 font-sans bg-emerald-900/50 px-2 py-0.5 rounded border border-emerald-700/50">
                      Channel: {aiMeta.channel}
                    </span>
                  ) : null;
                })()}
              </div>
            </div>

            {/* Model Trace & Latency */}
            {caseDetail.latest_prediction && (
              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                <span>Model: {caseDetail.latest_prediction.model_name}</span>
                <span>Hash: {caseDetail.latest_prediction.features_hash || "n/a"}</span>
              </div>
            )}
          </div>
        </div>

        {/* Policy Guardrails Gate */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            Policy Engine Authorization
          </div>
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Automated Attempts Check</span>
              <span className="font-mono font-medium text-slate-200">
                {caseDetail.attempt_count} / 2 allowed
              </span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Amount Limit (≤ ₹10,000)</span>
              <span className="font-mono font-medium text-slate-200">
                {caseDetail.amount_at_risk_paise <= 1000000 ? "PASSED (≤ ₹10k)" : "EXCEEDED (> ₹10k)"}
              </span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Minimum Probability (≥ 40%)</span>
              <span className="font-mono font-medium text-slate-200">
                {caseDetail.recovery_probability >= 0.4 ? "PASSED" : "BLOCKED"}
              </span>
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-slate-400">Opt-Out Guardrail</span>
              <span className="font-mono font-medium text-emerald-400">
                {caseDetail.customer?.opted_out ? "BLOCKED" : "CLEARED"}
              </span>
            </div>
            <div className="rounded-lg bg-slate-950 p-2.5 border border-slate-800 text-[11px] text-slate-400">
              <strong className="text-slate-300">Safety Rule:</strong> LLM never changes amount or overrides attempt limits. Controlled deterministically by application code.
            </div>
          </div>
        </div>
      </div>

      {/* Audit Trail Timeline */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <Clock className="h-4 w-4 text-sky-400" />
          Audit Trail & Traceability
        </h2>
        <p className="text-xs text-slate-400">
          Append-only verifiable ledger of every event, agent recommendation, policy evaluation, and webhook receipt.
        </p>

        <div className="space-y-4 pt-2">
          {caseDetail.audit_logs.length === 0 ? (
            <div className="text-xs text-slate-500 italic">No audit events recorded yet.</div>
          ) : (
            caseDetail.audit_logs.map((log) => (
              <div
                key={log.id}
                className="flex items-start gap-4 rounded-lg border border-slate-800/80 bg-slate-950/60 p-3.5 text-xs"
              >
                <div className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[10px] font-semibold text-slate-300">
                  {log.actor}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200 font-mono">{log.event_name}</span>
                    <span className="text-[11px] text-slate-500">{formatDate(log.created_at)}</span>
                  </div>
                  <p className="text-slate-400 leading-relaxed">{log.reason}</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
