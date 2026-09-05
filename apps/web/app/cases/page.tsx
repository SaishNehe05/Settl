import Link from "next/link";
import { ArrowRight, Filter, Search, Zap, Clock, ShieldCheck, CheckCircle2, Ban, AlertTriangle, CreditCard, ChevronRight } from "lucide-react";
import { fetchRecoveryCases, fetchReceivablesStatus } from "@/lib/api";
import { formatINR, formatPercent, formatDate } from "@/lib/utils";
import StatusBadge from "@/components/cases/status-badge";
import CreateManualCaseButton from "@/components/cases/create-manual-case-button";

interface CasesPageProps {
  searchParams: Promise<{ status?: string }>;
}

export const revalidate = 0;

export default async function CasesPage({ searchParams }: CasesPageProps) {
  const { status } = await searchParams;
  const [cases, receivablesStatus] = await Promise.all([
    fetchRecoveryCases(status),
    fetchReceivablesStatus(),
  ]);

  const statusFilters = [
    { label: "Active Pipeline", value: "" },
    { label: "Actioned", value: "ACTION_EXECUTED" },
    { label: "Awaiting Result", value: "WAITING_RESULT" },
    { label: "Requires Human", value: "ESCALATED" },
    { label: "Recovered", value: "RECOVERED" },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Recovery Queue
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Prioritized revenue-loss events requiring autonomous or human action.
          </p>
        </div>
        <CreateManualCaseButton />
      </div>

      {/* Receivables Integration State Banner */}
      {!receivablesStatus.connected && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-amber-500/10 p-2 border border-amber-500/20 text-amber-400 font-semibold font-mono text-[11px]">
              B2B
            </div>
            <div>
              <div className="font-semibold text-slate-200">Receivables integration not connected</div>
              <div className="text-slate-400 mt-0.5">
                No external ERP / accounting integration connected yet. Ingest real invoice events via <code className="text-sky-400 font-mono">POST /api/v1/receivables/events</code>.
              </div>
            </div>
          </div>
          <span className="rounded-full bg-slate-800/80 px-2.5 py-1 text-[10px] font-mono text-slate-400 border border-slate-700/60 whitespace-nowrap">
            0 Invoices Tracked
          </span>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800/80 pb-4">
        {statusFilters.map((tab) => {
          const isSelected = (!status && tab.value === "") || status === tab.value;
          return (
            <Link
              key={tab.value}
              href={tab.value ? `/cases?status=${tab.value}` : "/cases"}
              className={`rounded-full px-4 py-2 text-xs font-semibold transition-all ${isSelected
                  ? "bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-inner"
                  : "text-slate-400 bg-slate-900/50 border border-slate-800 hover:bg-slate-800 hover:text-slate-200"
                }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>

      {/* Rich Cases List */}
      <div className="space-y-3">
        {cases.length === 0 ? (
          <div className="rounded-xl border border-slate-800 border-dashed bg-slate-900/20 p-12 text-center flex flex-col items-center justify-center">
             <ShieldCheck className="h-10 w-10 text-slate-600 mb-3" />
             <h3 className="text-slate-300 font-medium text-sm">Inbox Zero</h3>
             <p className="text-slate-500 text-xs mt-1 max-w-[250px]">No leakage events match the current filter criteria.</p>
          </div>
        ) : (
          cases.map((c) => {
             const isRecovered = c.status === "RECOVERED";
             const isBlocked = c.status === "BLOCKED";
             const isEscalated = c.status === "ESCALATED";

             return (
              <Link 
                key={c.id} 
                href={`/cases/${c.id}`}
                className="block group rounded-xl border border-slate-800/60 bg-slate-900/40 hover:bg-slate-800/40 hover:border-slate-700/80 transition-all p-4 md:p-5 relative overflow-hidden"
              >
                {/* Accent line based on priority/status */}
                <div className={`absolute left-0 top-0 bottom-0 w-1 ${
                  isRecovered ? "bg-emerald-500" : 
                  isBlocked ? "bg-rose-500" : 
                  isEscalated ? "bg-purple-500" : 
                  "bg-sky-500"
                }`} />

                <div className="flex flex-col lg:flex-row gap-6 items-start lg:items-center justify-between ml-2">
                   
                   {/* Col 1: Customer & Type */}
                   <div className="flex-1 flex items-start gap-4 min-w-[240px]">
                      <div className="hidden sm:flex h-10 w-10 rounded-full bg-slate-800 border border-slate-700 items-center justify-center text-slate-400 font-bold text-sm shrink-0 uppercase">
                         {c.customer_name ? c.customer_name.charAt(0) : "?"}
                      </div>
                      <div>
                         <div className="flex items-center gap-2 mb-1">
                            <span className="font-semibold text-slate-200 group-hover:text-sky-400 transition-colors">
                              {c.customer_name || "Unknown Customer"}
                            </span>
                            <span className="text-[10px] text-slate-500 font-mono">
                              {c.id.split("-")[0]}...
                            </span>
                         </div>
                         <div className="flex flex-wrap items-center gap-1.5">
                            <span className={`rounded-full px-2 py-0.5 text-[9px] font-mono font-bold border ${c.source === 'simulation' || c.source === 'synthetic' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' : 'bg-sky-500/10 text-sky-400 border-sky-500/20'}`}>
                              {c.source === 'simulation' || c.source === 'synthetic' ? (c.source).toUpperCase() : 'RAZORPAY TEST'}
                            </span>
                            {c.subscription_id && (
                              <span className="rounded-full px-2 py-0.5 text-[9px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                SUB {c.provider_state === 'halted' ? 'HALTED' : 'FAILED'}
                              </span>
                            )}
                            {c.invoice_id && (
                              <span className="rounded-full px-2 py-0.5 text-[9px] font-mono font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                OVERDUE RECEIVABLE
                              </span>
                            )}
                         </div>
                      </div>
                   </div>

                   {/* Col 2: Financials & AI */}
                   <div className="flex-[0.8] flex flex-col sm:flex-row gap-6 w-full lg:w-auto border-t border-slate-800/60 lg:border-t-0 pt-4 lg:pt-0">
                      <div className="flex-1">
                        <div className="text-[10px] text-slate-500 font-medium uppercase mb-0.5">Amount at Risk</div>
                        <div className="font-semibold text-slate-200">
                          {formatINR(c.amount_at_risk_paise)}
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="text-[10px] text-slate-500 font-medium uppercase mb-1">AI Confidence</div>
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-sky-500 h-full rounded-full"
                              style={{ width: `${Math.min(c.recovery_probability * 100, 100)}%` }}
                            />
                          </div>
                          <span className="text-[11px] font-medium text-slate-400">
                            {Math.round(c.recovery_probability * 100)}%
                          </span>
                        </div>
                      </div>
                   </div>

                   {/* Col 3: Action & Status */}
                   <div className="flex-1 flex items-center justify-between w-full lg:w-auto gap-4 border-t border-slate-800/60 lg:border-t-0 pt-4 lg:pt-0">
                      <div className="flex flex-col gap-1.5">
                        <div className="text-[10px] text-slate-500 font-medium uppercase">Current Status</div>
                        <StatusBadge status={c.status} />
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <div className="hidden sm:flex flex-col items-end">
                           <span className="text-[10px] text-slate-500 font-medium uppercase mb-0.5">Recommended</span>
                           <span className="text-[11px] font-mono text-slate-300">
                             {c.recommended_action || (c.status === "NEW" || c.status === "ANALYZING" ? "ANALYZING..." : "N/A")}
                           </span>
                        </div>
                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 group-hover:bg-sky-900 group-hover:text-sky-400 transition-colors shrink-0">
                           <ChevronRight className="h-4 w-4" />
                        </div>
                      </div>
                   </div>

                </div>
              </Link>
             )
          })
        )}
      </div>
    </div>
  );
}
