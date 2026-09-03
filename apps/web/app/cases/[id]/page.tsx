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
  Zap,
  Info
} from "lucide-react";
import { fetchCaseDetail, fetchPolicy } from "@/lib/api";
import { formatINR, formatPercent, formatDate } from "@/lib/utils";
import StatusBadge from "@/components/cases/status-badge";
import CaseActions from "@/components/cases/case-actions";

interface CaseDetailPageProps {
  params: Promise<{ id: string }>;
}

export const revalidate = 0;

const formatAction = (action: string | null | undefined) => {
  if (!action) return null;
  const map: Record<string, string> = {
    "CREATE_PAYMENT_LINK": "Send Recovery Payment Link",
    "SEND_REMINDER": "Send Reminder",
    "WAIT": "Wait and Monitor",
    "MONITOR": "Wait and Monitor",
    "CUSTOMER_ACTION_REQUIRED": "Request Customer Action",
    "CREATE_COLLECTION_CASE": "Escalate to Internal Collections"
  };
  return map[action] || action.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
};

const formatRootCause = (cause: string | null | undefined) => {
  if (!cause) return "Not yet executed";
  const match = cause.match(/^\[(.*?)\] (.*)$/);
  if (match) {
    const category = match[1];
    const desc = match[2];
    let readableCategory = category;
    if (category === "BANK_TECHNICAL") readableCategory = "Likely bank or network issue";
    if (category === "CUSTOMER_ABANDONED") readableCategory = "Customer abandoned checkout";
    if (category === "INSUFFICIENT_FUNDS") readableCategory = "Insufficient funds";
    if (category === "FRAUD_SUSPICION") readableCategory = "Suspected fraud / Risk blocked";
    return (
      <>
        <div className="font-semibold text-slate-200">{readableCategory}</div>
        <details className="mt-2 text-[10px] text-slate-500 cursor-pointer">
          <summary className="hover:text-slate-400 select-none">View technical details</summary>
          <div className="mt-1.5 p-2 bg-slate-950/50 rounded border border-slate-800/50">
            <div>{desc}</div>
            <div className="font-mono mt-1 text-[9px]">Code: {category}</div>
          </div>
        </details>
      </>
    );
  }
  return cause;
};

export default async function CaseDetailPage({ params }: CaseDetailPageProps) {
  const { id } = await params;
  const caseDetail = await fetchCaseDetail(id);
  const policy = await fetchPolicy().catch(() => null);

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
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono">{caseDetail.id}</h1>
            <StatusBadge status={caseDetail.status} />
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300 font-medium">
              {caseDetail.priority} Priority
            </span>
            <span className={`rounded-md px-2 py-1 text-[10px] font-mono font-bold tracking-wider border ${caseDetail.source === 'synthetic' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' : 'bg-sky-500/10 text-sky-400 border-sky-500/20'}`}>
              Source: {caseDetail.source === 'synthetic' ? 'SYNTHETIC' : 'RAZORPAY TEST MODE'}
            </span>
          </div>
          <div className="flex items-center gap-5">
            <CaseActions 
              caseId={caseDetail.id} 
              status={caseDetail.status} 
              eventType={caseDetail.event_type}
              actualAction={caseDetail.actual_action}
            />
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

      {/* Phase 4: Verified Recovery Banner */}
      {caseDetail.status === "RECOVERED" && (
        <div className="rounded-xl border border-emerald-600/50 bg-emerald-950/40 p-5 backdrop-blur-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="rounded-xl bg-emerald-500/20 p-2.5 border border-emerald-500/30">
              <CheckCircle2 className="h-6 w-6 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white">Revenue Successfully Recovered</h3>
                <span className="rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[10px] font-mono text-emerald-300 font-semibold border border-emerald-500/40">
                  VERIFIED WEBHOOK PROOF
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-0.5">
                Payment verified via Razorpay webhook signature. Amount credited to merchant ledger.
              </p>
            </div>
          </div>
          <div className="sm:text-right">
            <span className="text-xs text-emerald-300/80">Recovered Amount</span>
            <div className="text-2xl font-extrabold text-emerald-400 font-mono">
              {formatINR(caseDetail.amount_recovered_paise)}
            </div>
          </div>
        </div>
      )}

      {/* Phase 4: Active Razorpay Payment Link Card */}
      {(() => {
        const plinkId = caseDetail.payment_link_id;
        const shortUrl = caseDetail.payment_link_url;
        const notifStatus = caseDetail.notification_status;
        const paymentId = caseDetail.payment_id;

        if (!plinkId && caseDetail.status !== "WAITING_RESULT") return null;

        return (
          <div className="rounded-xl border border-sky-600/40 bg-sky-950/30 p-4 space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-sky-500/10 p-2 border border-sky-500/30 text-sky-400">
                  <ExternalLink className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-white">Active Razorpay Payment Link</span>
                    <span className="rounded bg-sky-500/20 text-sky-300 text-[10px] font-mono px-2 py-0.5">
                      TEST MODE
                    </span>
                  </div>
                  {shortUrl && (
                    <div className="text-xs font-mono text-sky-300 mt-1 select-all hover:underline">
                      {shortUrl}
                    </div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {shortUrl && (
                  <a
                    href={shortUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg border border-sky-600/60 bg-sky-900/40 px-3 py-1.5 text-xs font-medium text-sky-200 hover:bg-sky-800/60 transition-colors"
                  >
                    Open Link
                    <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>
            {/* Detail rows */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-sky-800/40 text-[11px]">
              {plinkId && (
                <div>
                  <div className="text-slate-500">Payment Link ID</div>
                  <div className="font-mono text-slate-300 mt-0.5 truncate">{plinkId}</div>
                </div>
              )}
              {paymentId && (
                <div>
                  <div className="text-slate-500">Original Payment ID</div>
                  <div className="font-mono text-slate-300 mt-0.5 truncate">{paymentId}</div>
                </div>
              )}
              <div>
                <div className="text-slate-500">Notification</div>
                <div className={`font-mono font-medium mt-0.5 ${notifStatus === "SENT" || notifStatus === "DELIVERED" ? "text-emerald-400" : notifStatus === "FAILED" ? "text-rose-400" : "text-amber-400"}`}>
                  {notifStatus || "Not yet executed"}
                </div>
              </div>
              <div>
                <div className="text-slate-500">Customer Contact</div>
                <div className="text-slate-300 mt-0.5 truncate">{caseDetail.customer?.email || "Not available"}</div>
              </div>
            </div>
          </div>
        );
      })()}
      
      {/* What Happens Next */}
      <div className="rounded-xl border border-indigo-500/20 bg-indigo-950/20 p-5 backdrop-blur-sm space-y-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
          <Info className="h-4 w-4" /> What Happens Next
        </h3>
        <p className="text-sm text-slate-300 leading-relaxed font-medium">
          {(() => {
            if (caseDetail.status === "WAITING_RESULT") return "Waiting for customer payment. A valid Razorpay Payment Link is active.";
            if (caseDetail.status === "RECOVERED") return "Payment confirmed and recovery verified.";
            if (caseDetail.status === "ESCALATED") return "Needs merchant review to proceed.";
            if (caseDetail.status === "BLOCKED" || caseDetail.status === "STOPPED") return "Recovery stopped. No further automated attempts are allowed.";
            if (caseDetail.status === "NEW" || caseDetail.status === "ANALYZING") return "Analyzing failure event to determine the best recovery action.";
            if (caseDetail.status === "APPROVED") return "Authorized to execute recovery action.";
            if (caseDetail.attempt_count >= (policy?.max_attempts || 0) && caseDetail.status !== "WAITING_RESULT") return "Maximum automated attempts reached.";
            return "Pending evaluation.";
          })()}
        </p>
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
                {caseDetail.customer?.name || caseDetail.customer_name || "Not available"}
              </div>
            </div>
            <div>
              <div className="text-slate-500">Contact</div>
              <div className="text-slate-300 font-mono mt-0.5">
                {caseDetail.customer?.email || caseDetail.customer_email || "Not available"}
              </div>
              <div className="text-slate-400 font-mono mt-0.5">
                {caseDetail.customer?.phone || "Not available"}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800">
              <div>
                <div className="text-slate-500">Payment Success Rate</div>
                <div className={`font-semibold text-sm mt-0.5 ${caseDetail.customer?.success_rate != null ? 'text-emerald-400' : 'text-slate-500 font-normal italic'}`}>
                  {caseDetail.customer?.success_rate != null ? formatPercent(caseDetail.customer.success_rate) : "Limited history"}
                </div>
              </div>
              <div>
                <div className="text-slate-500">Customer Tier</div>
                <div className={`font-semibold text-sm mt-0.5 ${(caseDetail.customer?.customer_value && caseDetail.customer.customer_value !== "UNKNOWN") ? 'text-purple-400' : 'text-slate-500 font-normal italic'}`}>
                  {(!caseDetail.customer?.customer_value || caseDetail.customer.customer_value === "UNKNOWN") ? "No previous history" : caseDetail.customer.customer_value}
                </div>
              </div>
            </div>
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
              <span className="text-slate-500">Communication Opt-Out</span>
              {caseDetail.customer ? (
                <span className={`font-medium ${caseDetail.customer.opted_out ? "text-rose-400" : "text-emerald-400"}`}>
                  {caseDetail.customer.opted_out ? "Opted Out" : "Consent Active"}
                </span>
              ) : (
                <span className="font-medium text-slate-500 italic">Not available</span>
              )}
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
              {caseDetail.recovery_probability > 0 ? (
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xl font-bold text-sky-400 font-mono">
                    {formatPercent(caseDetail.recovery_probability)}
                  </span>
                  <span className="text-[11px] text-slate-400">
                    (Calibrated Risk Model)
                  </span>
                </div>
              ) : (
                <div className="text-slate-400 italic mt-1">Not available</div>
              )}
            </div>
            <div>
              <div className="text-slate-500">Diagnostic Root Cause</div>
              <div className={`mt-1 bg-slate-950 px-3 py-2 rounded-lg border border-slate-800 font-sans ${!caseDetail.root_cause ? 'text-slate-500 italic' : ''}`}>
                {formatRootCause(caseDetail.root_cause)}
              </div>
            </div>

            {/* Structured Evidence Tags removed to reduce text density */}

            <div>
              <div className="text-slate-500">Decision Agent Recommendation</div>
              {caseDetail.recommended_action ? (
                <div className="flex items-center justify-between font-semibold text-emerald-400 mt-1 bg-emerald-950/30 px-3 py-2 rounded-lg border border-emerald-800/50">
                  <span>{formatAction(caseDetail.recommended_action)}</span>
                </div>
              ) : (
                <div className="mt-1 text-slate-500 italic">Not yet executed</div>
              )}
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
          {(() => {
            const policyLog = caseDetail.audit_logs.find(log => log.event_name.startsWith('POLICY_'));
            let decision = "WAITING";
            let explanation = "Policy has not been evaluated yet.";
            if (policyLog) {
                decision = policyLog.event_name.replace('POLICY_', '');
                explanation = policyLog.reason || explanation;
            }
            
            return (
              <div className="space-y-3 text-xs">
                <div className="flex items-center justify-between py-2 border-b border-slate-800/60">
                  <span className="text-slate-400 font-semibold">Policy Decision</span>
                  <span className={`font-bold flex items-center gap-1.5 ${decision === "ALLOW" ? "text-emerald-400" : decision === "WAITING" ? "text-amber-400" : "text-rose-400"}`}>
                    {decision === "ALLOW" ? <CheckCircle2 className="h-4 w-4" /> : null}
                    {decision === "ALLOW" ? "Approved" : decision}
                  </span>
                </div>
                
                {policy && (
                  <>
                    <div className="flex flex-col py-2 border-b border-slate-800/60">
                      <span className="text-slate-400">Amount</span>
                      <div className="flex items-center gap-2 mt-0.5 text-slate-200">
                        {caseDetail.amount_at_risk_paise <= policy.max_automated_amount_paise ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                        ) : (
                          <span className="text-rose-400 font-bold px-1">X</span>
                        )}
                        <span>Within automated limit (≤ {formatINR(policy.max_automated_amount_paise)})</span>
                      </div>
                    </div>
                    
                    <div className="flex flex-col py-2 border-b border-slate-800/60">
                      <span className="text-slate-400">Attempts</span>
                      <div className="flex items-center gap-2 mt-0.5 text-slate-200">
                        {caseDetail.attempt_count <= policy.max_attempts ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                        ) : (
                          <span className="text-rose-400 font-bold px-1">X</span>
                        )}
                        <span>{caseDetail.attempt_count} of {policy.max_attempts}</span>
                      </div>
                    </div>

                    <div className="flex flex-col py-2 border-b border-slate-800/60">
                      <span className="text-slate-400">Minimum Probability</span>
                      <div className="flex items-center gap-2 mt-0.5 text-slate-200">
                        {caseDetail.recovery_probability >= policy.min_probability ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                        ) : (
                          <span className="text-rose-400 font-bold px-1">X</span>
                        )}
                        <span>Meets {formatPercent(policy.min_probability)} threshold</span>
                      </div>
                    </div>

                    <div className="flex flex-col py-2 border-b border-slate-800/60">
                      <span className="text-slate-400">Customer Consent</span>
                      <div className="flex items-center gap-2 mt-0.5 text-slate-200">
                        {(!caseDetail.customer || !caseDetail.customer.opted_out) ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                        ) : (
                          <span className="text-rose-400 font-bold px-1">X</span>
                        )}
                        <span>Contact allowed</span>
                      </div>
                    </div>
                  </>
                )}
              </div>
            );
          })()}
        </div>
      </div>

      {/* Audit Trail Timeline */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
        <h2 className="text-base font-semibold text-white flex items-center gap-2">
          <Clock className="h-4 w-4 text-sky-400" />
          Technical Details & Audit Trail
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
