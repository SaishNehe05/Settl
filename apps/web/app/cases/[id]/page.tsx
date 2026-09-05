import Link from "next/link";
import { notFound } from "next/navigation";
import { 
  ArrowLeft, 
  ArrowRight,
  CheckCircle2, 
  Clock, 
  ExternalLink, 
  FileText, 
  Layers, 
  Lock, 
  ShieldCheck, 
  UserCheck, 
  Zap,
  Info,
  CalendarDays,
  Activity,
  Ban,
  ChevronRight,
  ChevronDown
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
      <div className="space-y-1">
        <div className="font-semibold text-slate-200">{readableCategory}</div>
        <div className="text-slate-400 text-xs">{desc}</div>
      </div>
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

  const isRecovered = caseDetail.status === "RECOVERED";
  const isBlocked = caseDetail.status === "BLOCKED" || caseDetail.status === "STOPPED";
  const isEscalated = caseDetail.status === "ESCALATED";

  return (
    <div className="space-y-8 pb-12 max-w-5xl mx-auto">
      {/* Navigation & Header */}
      <div>
        <Link
          href="/cases"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-sky-400 transition-colors mb-4"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to Recovery Queue
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl font-bold tracking-tight text-white font-mono flex items-center gap-3">
              {caseDetail.id}
            </h1>
            <StatusBadge status={caseDetail.status} />
            <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-mono font-bold tracking-wider border ${caseDetail.source === 'synthetic' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' : 'bg-sky-500/10 text-sky-400 border-sky-500/20'}`}>
              {caseDetail.source === 'synthetic' ? 'SYNTHETIC EVENT' : 'RAZORPAY TEST MODE'}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <CaseActions caseDetail={caseDetail} />
          </div>
        </div>
      </div>

      {/* Top Banner: Status Outcome */}
      <div className={`rounded-2xl border p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-6 relative overflow-hidden ${
        isRecovered ? "bg-emerald-950/30 border-emerald-900/50" :
        isBlocked ? "bg-rose-950/30 border-rose-900/50" :
        isEscalated ? "bg-purple-950/30 border-purple-900/50" :
        "bg-slate-900/50 border-slate-800"
      }`}>
        <div className="absolute right-0 top-0 bottom-0 w-64 bg-gradient-to-l from-current opacity-5 pointer-events-none" 
             style={{ color: isRecovered ? '#10b981' : isBlocked ? '#f43f5e' : isEscalated ? '#a855f7' : '#38bdf8' }} />
        
        <div className="flex items-center gap-4 relative z-10">
           <div className={`w-12 h-12 rounded-full flex items-center justify-center border shadow-lg ${
             isRecovered ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400" :
             isBlocked ? "bg-rose-500/20 border-rose-500/30 text-rose-400" :
             isEscalated ? "bg-purple-500/20 border-purple-500/30 text-purple-400" :
             "bg-sky-500/20 border-sky-500/30 text-sky-400"
           }`}>
              {isRecovered ? <CheckCircle2 className="h-6 w-6" /> :
               isBlocked ? <Ban className="h-6 w-6" /> :
               isEscalated ? <UserCheck className="h-6 w-6" /> :
               <Activity className="h-6 w-6" />}
           </div>
           <div>
             <h2 className="text-lg font-bold text-white">
               {isRecovered ? "Revenue Successfully Recovered" :
                isBlocked ? "Recovery Blocked by Guardrails" :
                isEscalated ? "Escalated for Human Review" :
                "Recovery in Progress"}
             </h2>
             <p className="text-sm text-slate-400 mt-1 max-w-xl">
                {caseDetail.invoice_id ? 
                  "B2B Overdue Invoice recovery workflow." : 
                  caseDetail.subscription_id ? "Subscription failure recovery workflow." : "Standard payment failure recovery workflow."}
             </p>
           </div>
        </div>
        
        <div className="relative z-10 text-left sm:text-right">
           <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
             {isRecovered ? "Amount Recovered" : "Amount at Risk"}
           </div>
           <div className={`text-3xl font-extrabold tracking-tight ${
             isRecovered ? "text-emerald-400" : "text-white"
           }`}>
             {formatINR(isRecovered ? caseDetail.amount_recovered_paise : caseDetail.amount_at_risk_paise)}
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* What Happened (Context) */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="flex items-center gap-2 mb-6">
             <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400">
               <FileText className="h-4 w-4" />
             </div>
             <h3 className="text-base font-semibold text-white">What Happened</h3>
          </div>
          
          <div className="space-y-4">
             <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-950/50 rounded-lg p-3 border border-slate-800/60">
                   <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">Customer</div>
                   <div className="font-medium text-slate-200">{caseDetail.customer?.name || caseDetail.customer_name || "Unknown"}</div>
                   <div className="text-xs text-slate-400 mt-0.5">{caseDetail.customer?.email || caseDetail.customer_email || ""}</div>
                </div>
                <div className="bg-slate-950/50 rounded-lg p-3 border border-slate-800/60">
                   <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">Status</div>
                   <div className={`font-medium ${caseDetail.customer?.opted_out ? 'text-rose-400' : 'text-emerald-400'}`}>
                     {caseDetail.customer?.opted_out ? 'Opted out of comms' : 'Consent active'}
                   </div>
                   <div className="text-xs text-slate-400 mt-0.5">Tier: {caseDetail.customer?.customer_value || "Unknown"}</div>
                </div>
             </div>

             {caseDetail.invoice_id && (
                <div className="bg-indigo-950/20 rounded-lg p-3 border border-indigo-900/30">
                   <div className="text-[10px] uppercase font-semibold text-indigo-400 mb-2">Invoice Details</div>
                   <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-300 font-mono">{caseDetail.external_invoice_id || caseDetail.invoice_id}</span>
                      <span className="text-amber-400 font-medium">{caseDetail.days_overdue} days overdue</span>
                   </div>
                </div>
             )}
             
             {caseDetail.subscription_id && (
                <div className="bg-amber-950/20 rounded-lg p-3 border border-amber-900/30">
                   <div className="text-[10px] uppercase font-semibold text-amber-400 mb-2">Subscription Details</div>
                   <div className="flex justify-between items-center text-sm">
                      <span className="text-slate-300 font-mono">{caseDetail.subscription_id}</span>
                      <span className="text-slate-300 uppercase">State: {caseDetail.provider_state}</span>
                   </div>
                </div>
             )}
          </div>
        </div>

        {/* Why Settl Acted (AI) */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="flex items-center gap-2 mb-6">
             <div className="w-8 h-8 rounded-lg bg-sky-900/30 border border-sky-800/40 flex items-center justify-center text-sky-400">
               <Zap className="h-4 w-4" />
             </div>
             <h3 className="text-base font-semibold text-white">Why Settl Acted</h3>
          </div>

          <div className="space-y-4">
             <div className="bg-slate-950/50 rounded-lg p-4 border border-slate-800/60">
                <div className="flex justify-between items-start mb-3">
                   <div className="text-[10px] uppercase font-semibold text-slate-500">Root Cause Diagnostics</div>
                   <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/50 px-2 py-0.5 rounded border border-emerald-900/50">
                     {caseDetail.latest_prediction?.validation_status || "VALID"}
                   </span>
                </div>
                {formatRootCause(caseDetail.root_cause)}
             </div>

             <div className="flex gap-4">
                <div className="flex-1 bg-slate-950/50 rounded-lg p-3 border border-slate-800/60 flex flex-col justify-center">
                   <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">Recovery Probability</div>
                   <div className="text-2xl font-bold text-sky-400">
                     {Math.round(caseDetail.recovery_probability * 100)}%
                   </div>
                </div>
                <div className="flex-[2] bg-slate-950/50 rounded-lg p-3 border border-slate-800/60">
                   <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1">AI Recommendation</div>
                   <div className="font-semibold text-slate-200 mt-1 text-sm">
                     {formatAction(caseDetail.recommended_action) || "Analyzing..."}
                   </div>
                </div>
             </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Policy Decision */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="flex items-center gap-2 mb-6">
             <div className="w-8 h-8 rounded-lg bg-emerald-900/30 border border-emerald-800/40 flex items-center justify-center text-emerald-400">
               <ShieldCheck className="h-4 w-4" />
             </div>
             <h3 className="text-base font-semibold text-white">Policy Decision</h3>
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
              <div className="space-y-4">
                <div className="bg-slate-950/50 rounded-lg p-4 border border-slate-800/60">
                   <div className="flex items-center justify-between mb-2">
                     <span className="text-[10px] uppercase font-semibold text-slate-500">Guardrail Engine Outcome</span>
                     <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                       decision === "ALLOW" ? "bg-emerald-950/50 text-emerald-400 border-emerald-900/50" : 
                       decision === "WAITING" ? "bg-amber-950/50 text-amber-400 border-amber-900/50" : 
                       "bg-rose-950/50 text-rose-400 border-rose-900/50"
                     }`}>
                       {decision === "ALLOW" ? "APPROVED" : decision}
                     </span>
                   </div>
                   <p className="text-sm text-slate-300 font-medium">{explanation}</p>
                </div>

                {policy && (
                  <div className="grid grid-cols-3 gap-2">
                     <div className="bg-slate-950/50 rounded-lg p-2.5 border border-slate-800/60 text-center">
                        <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1 flex items-center justify-center gap-1">
                          Amount {caseDetail.amount_at_risk_paise <= policy.max_automated_amount_paise ? <CheckCircle2 className="w-3 h-3 text-emerald-500" /> : <Ban className="w-3 h-3 text-rose-500" />}
                        </div>
                        <div className="text-xs text-slate-300">Within limits</div>
                     </div>
                     <div className="bg-slate-950/50 rounded-lg p-2.5 border border-slate-800/60 text-center">
                        <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1 flex items-center justify-center gap-1">
                          Attempts {caseDetail.attempt_count < policy.max_attempts ? <CheckCircle2 className="w-3 h-3 text-emerald-500" /> : <Ban className="w-3 h-3 text-rose-500" />}
                        </div>
                        <div className="text-xs text-slate-300">{caseDetail.attempt_count} of {policy.max_attempts}</div>
                     </div>
                     <div className="bg-slate-950/50 rounded-lg p-2.5 border border-slate-800/60 text-center">
                        <div className="text-[10px] uppercase font-semibold text-slate-500 mb-1 flex items-center justify-center gap-1">
                          Consent {(!caseDetail.customer || !caseDetail.customer.opted_out) ? <CheckCircle2 className="w-3 h-3 text-emerald-500" /> : <Ban className="w-3 h-3 text-rose-500" />}
                        </div>
                        <div className="text-xs text-slate-300">Verified</div>
                     </div>
                  </div>
                )}
              </div>
            );
          })()}
        </div>

        {/* What Settl Did (Execution) */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 flex flex-col">
          <div className="flex items-center gap-2 mb-6">
             <div className="w-8 h-8 rounded-lg bg-indigo-900/30 border border-indigo-800/40 flex items-center justify-center text-indigo-400">
               <Activity className="h-4 w-4" />
             </div>
             <h3 className="text-base font-semibold text-white">What Settl Did</h3>
          </div>
          
          <div className="flex-1 space-y-3">
             {/* Promise logic */}
             {caseDetail.promises && caseDetail.promises.length > 0 ? (
                <div className={`bg-slate-950/50 rounded-lg p-4 border border-slate-800/60 flex items-start gap-3`}>
                  <CalendarDays className={`h-5 w-5 mt-0.5 ${
                    caseDetail.promises[0].status === 'BROKEN' ? 'text-rose-400' :
                    caseDetail.promises[0].status === 'FULFILLED' ? 'text-emerald-400' :
                    'text-indigo-400'
                  }`} />
                  <div>
                    <div className="text-sm font-semibold text-white">Customer Promise Logged</div>
                    <div className="text-xs text-slate-400 mt-1">
                      Promised to pay {formatINR(caseDetail.promises[0].promised_amount_paise)} by {new Date(caseDetail.promises[0].promise_date).toLocaleDateString()}.
                    </div>
                    <div className={`text-[10px] font-mono font-bold mt-2 uppercase ${
                      caseDetail.promises[0].status === 'BROKEN' ? 'text-rose-400' :
                      caseDetail.promises[0].status === 'FULFILLED' ? 'text-emerald-400' :
                      'text-indigo-400'
                    }`}>
                      STATUS: {caseDetail.promises[0].status}
                    </div>
                  </div>
                </div>
             ) : null}

             {/* Link logic */}
             {caseDetail.payment_link_url ? (
                <div className="bg-slate-950/50 rounded-lg p-4 border border-slate-800/60 flex flex-col">
                  <div className="flex items-start gap-3 mb-3">
                     <ExternalLink className="h-5 w-5 mt-0.5 text-sky-400" />
                     <div>
                       <div className="text-sm font-semibold text-white">Payment Link Dispatched</div>
                       <div className="text-xs text-slate-400 mt-1">
                         A unique recovery checkout link was created and sent via {caseDetail.notification_status === "SENT" ? "email" : "system"}.
                       </div>
                     </div>
                  </div>
                  <a href={caseDetail.payment_link_url} target="_blank" rel="noreferrer" className="mt-auto bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold py-2 px-4 rounded flex items-center justify-center gap-2 transition-colors">
                     View Payment Checkout <ArrowRight className="h-3 w-3" />
                  </a>
                </div>
             ) : (
                !caseDetail.promises?.length && (
                  <div className="bg-slate-950/50 rounded-lg p-6 border border-slate-800/60 text-center flex flex-col items-center justify-center h-full">
                     <Clock className="h-6 w-6 text-slate-500 mb-2" />
                     <div className="text-sm font-medium text-slate-300">Pending Execution</div>
                     <div className="text-xs text-slate-500 mt-1">Awaiting policy gate or external systems.</div>
                  </div>
                )
             )}
          </div>
        </div>
      </div>

      {/* Recovery Timeline (Audit Trail) */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-base font-semibold text-white flex items-center gap-2 mb-6">
          <Clock className="h-4 w-4 text-sky-400" />
          Recovery Timeline
        </h2>

        <div className="relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-800 before:to-transparent space-y-6">
          {caseDetail.audit_logs.length === 0 ? (
            <div className="text-xs text-slate-500 italic text-center">No timeline events recorded yet.</div>
          ) : (
            caseDetail.audit_logs.map((log, idx) => {
               // Determine icon based on actor/event
               let Icon = Clock;
               let color = "text-slate-400";
               let bgClass = "bg-slate-950 border-slate-800";
               
               if (log.actor === "SYSTEM") {
                  Icon = Zap;
                  color = "text-sky-400";
                  bgClass = "bg-sky-950 border-sky-900/50";
               } else if (log.actor === "POLICY_ENGINE") {
                  Icon = ShieldCheck;
                  color = log.event_name === "POLICY_ALLOW" ? "text-emerald-400" : "text-rose-400";
                  bgClass = log.event_name === "POLICY_ALLOW" ? "bg-emerald-950 border-emerald-900/50" : "bg-rose-950 border-rose-900/50";
               } else if (log.actor === "WEBHOOK") {
                  Icon = CheckCircle2;
                  color = "text-emerald-400";
                  bgClass = "bg-emerald-950 border-emerald-900/50";
               } else if (log.actor === "USER") {
                  Icon = UserCheck;
                  color = "text-indigo-400";
                  bgClass = "bg-indigo-950 border-indigo-900/50";
               }

               return (
                <div key={log.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                  <div className={`flex items-center justify-center w-10 h-10 rounded-full border shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 relative z-10 ${bgClass}`}>
                     <Icon className={`h-4 w-4 ${color}`} />
                  </div>
                  <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-slate-800/60 bg-slate-900/50 backdrop-blur-sm shadow hover:bg-slate-800/50 transition-colors">
                     <div className="flex items-center justify-between mb-1">
                        <div className={`text-[10px] font-bold font-mono uppercase tracking-wider ${color}`}>
                           {log.event_name.replace(/_/g, " ")}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">
                           {formatDate(log.created_at)}
                        </div>
                     </div>
                     <p className="text-xs text-slate-300 leading-relaxed font-medium mt-2">{log.reason}</p>
                     <div className="text-[9px] text-slate-600 font-mono mt-3 uppercase">ACTOR: {log.actor}</div>
                  </div>
                </div>
               )
            })
          )}
        </div>
      </div>

      {/* Technical Details Accordion */}
      <details className="group rounded-xl border border-slate-800 bg-slate-900/20 [&_summary::-webkit-details-marker]:hidden">
         <summary className="flex cursor-pointer items-center justify-between p-4 font-semibold text-slate-400 hover:text-slate-300 transition-colors select-none">
            <div className="flex items-center gap-2">
               <Layers className="h-4 w-4" />
               Raw Technical Details
            </div>
            <ChevronDown className="h-4 w-4 transition duration-300 group-open:-rotate-180" />
         </summary>
         <div className="p-4 pt-0 border-t border-slate-800/50 mt-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[10px] font-mono text-slate-500">
               <div className="space-y-1">
                  <div><strong>ID:</strong> {caseDetail.id}</div>
                  <div><strong>Source:</strong> {caseDetail.source}</div>
                  <div><strong>Created:</strong> {caseDetail.created_at}</div>
                  <div><strong>Updated:</strong> {caseDetail.updated_at}</div>
               </div>
               <div className="space-y-1">
                  <div><strong>Model Name:</strong> {caseDetail.latest_prediction?.model_name || "N/A"}</div>
                  <div><strong>Model Version:</strong> {caseDetail.latest_prediction?.model_version || "N/A"}</div>
                  <div><strong>Features Hash:</strong> {caseDetail.latest_prediction?.features_hash || "N/A"}</div>
                  <div><strong>Raw Prob:</strong> {caseDetail.latest_prediction?.probability || "N/A"}</div>
               </div>
            </div>
         </div>
      </details>
    </div>
  );
}
