import Link from "next/link";
import { 
  AlertTriangle, 
  ArrowUpRight, 
  CheckCircle2, 
  DollarSign, 
  ShieldAlert, 
  Zap,
  ArrowRight,
  Activity,
  Clock,
  ShieldCheck,
  CreditCard,
  Ban
} from "lucide-react";
import { fetchDashboardSummary } from "@/lib/api";
import { formatINR, formatPercent } from "@/lib/utils";
import StatusBadge from "@/components/cases/status-badge";
import { MerchantName } from "@/components/auth/merchant-name";

export const revalidate = 0; // Fresh data per request

interface DashboardPageProps {
  searchParams: Promise<{ mode?: string }>;
}

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const { mode } = await searchParams;
  const summary = await fetchDashboardSummary(mode);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            Recovery Command Center
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time autonomous revenue recovery overview for{" "}
            <span className="text-slate-700 font-medium"><MerchantName /></span>.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/cases"
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-500 transition-colors shadow-sm"
          >
            View Recovery Queue
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* Recovery Performance Block */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-1 rounded-xl border border-slate-200 bg-white p-5 flex flex-col justify-between hover:border-slate-300 hover:shadow-sm transition-all">
          <div>
            <div className="flex items-center gap-2 text-slate-500 mb-2">
              <AlertTriangle className="h-4 w-4 text-rose-500" />
              <h3 className="text-sm font-medium">Revenue at Risk</h3>
            </div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">
              {formatINR(summary.revenue_at_risk_paise)}
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-500">
              <span className="text-rose-600 font-medium">{summary.total_cases_count}</span> leakage events detected
            </p>
          </div>
        </div>

        <div className="lg:col-span-1 rounded-xl border border-slate-200 bg-white p-5 flex flex-col justify-between hover:border-slate-300 hover:shadow-sm transition-all">
          <div>
            <div className="flex items-center gap-2 text-slate-500 mb-2">
              <ShieldCheck className="h-4 w-4 text-indigo-500" />
              <h3 className="text-sm font-medium">Eligible Revenue</h3>
            </div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">
              {formatINR(summary.eligible_revenue_paise)}
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-500">
               Approved for recovery by policy
            </p>
          </div>
        </div>

        <div className="lg:col-span-2 rounded-xl border border-emerald-200 bg-emerald-50/50 p-5 flex flex-col justify-between relative overflow-hidden group hover:border-emerald-300 hover:shadow-sm transition-all">
          <div className="absolute -top-24 -right-24 p-32 bg-emerald-200/30 blur-[80px] rounded-full group-hover:bg-emerald-200/50 transition-colors duration-500" />
          <div className="relative z-10 flex flex-col sm:flex-row gap-6 justify-between h-full">
             <div className="flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 text-slate-500 mb-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <h3 className="text-sm font-medium">Verified Recovered</h3>
                  </div>
                  <div className="text-4xl font-bold text-slate-900 tracking-tight">
                    {formatINR(summary.revenue_recovered_paise)}
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-emerald-200/60">
                  <p className="text-xs text-emerald-700/70">
                    <span className="text-emerald-700 font-medium">{summary.recovered_cases_count}</span> cases successfully closed
                  </p>
                </div>
             </div>
             
             <div className="flex-1 flex flex-col justify-center border-l border-emerald-200/60 pl-6">
                 <div className="text-sm font-medium text-emerald-700/60 mb-1">Recovery Rate</div>
                 <div className="text-3xl font-bold text-emerald-600">{formatPercent(summary.recovery_rate)}</div>
                 <div className="text-xs text-emerald-700/40 mt-1">Recovered vs Eligible pipeline</div>
             </div>
          </div>
        </div>
      </div>

      {/* Recovery Pipeline Funnel */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 overflow-hidden relative">
         <h2 className="text-base font-semibold text-slate-900 mb-6 flex items-center gap-2">
           <Activity className="h-4 w-4 text-indigo-500" />
           Recovery Pipeline
         </h2>
         
         <div className="flex flex-col md:flex-row justify-between items-stretch gap-2 text-center relative z-10">
           {/* Step 1 */}
           <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col items-center justify-center relative hover:bg-slate-100 transition-colors">
             <AlertTriangle className="h-5 w-5 text-rose-500 mb-2" />
             <div className="text-xs font-semibold text-slate-700">AT RISK</div>
             <div className="text-[10px] text-slate-400 mt-1">Leakage Event Ingested</div>
             <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-slate-300 z-20">
               <ArrowRight className="h-4 w-4" />
             </div>
           </div>
           
           {/* Step 2 */}
           <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col items-center justify-center relative hover:bg-slate-100 transition-colors">
             <ShieldCheck className="h-5 w-5 text-indigo-500 mb-2" />
             <div className="text-xs font-semibold text-slate-700">ELIGIBLE</div>
             <div className="text-[10px] text-slate-400 mt-1">Passed Policy Gate</div>
             <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-slate-300 z-20">
               <ArrowRight className="h-4 w-4" />
             </div>
           </div>

           {/* Step 3 */}
           <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col items-center justify-center relative hover:bg-slate-100 transition-colors">
             <Zap className="h-5 w-5 text-violet-500 mb-2" />
             <div className="text-xs font-semibold text-slate-700">ACTIONED</div>
             <div className="text-[10px] text-slate-400 mt-1">Autonomous Outreach</div>
             <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-slate-300 z-20">
               <ArrowRight className="h-4 w-4" />
             </div>
           </div>

           {/* Step 4 */}
           <div className="flex-1 bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col items-center justify-center relative hover:bg-slate-100 transition-colors">
             <CreditCard className="h-5 w-5 text-amber-500 mb-2" />
             <div className="text-xs font-semibold text-slate-700">AWAITING PAYMENT</div>
             <div className="text-[10px] text-slate-400 mt-1">Link Sent to Customer</div>
             <div className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 text-slate-300 z-20">
               <ArrowRight className="h-4 w-4" />
             </div>
           </div>

           {/* Step 5 */}
           <div className="flex-1 bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex flex-col items-center justify-center hover:bg-emerald-100 transition-colors">
             <CheckCircle2 className="h-5 w-5 text-emerald-600 mb-2" />
             <div className="text-xs font-semibold text-emerald-700">VERIFIED</div>
             <div className="text-[10px] text-emerald-500 mt-1">Webhook Reconciled</div>
           </div>
         </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Recovery Pipeline Table */}
        <div className="lg:col-span-2 rounded-xl border border-slate-200 bg-white flex flex-col overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900">Active Recovery Queue</h2>
              <p className="text-xs text-slate-500 mt-0.5">Prioritized cases requiring attention.</p>
            </div>
            <Link
              href="/cases"
              className="flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-500 transition-colors"
            >
              View all {summary.total_cases_count}
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-100 bg-slate-50/80 text-slate-500">
                <tr>
                  <th className="px-6 py-4 font-medium">Customer & ID</th>
                  <th className="px-6 py-4 font-medium">Risk Amount</th>
                  <th className="px-6 py-4 font-medium">AI Confidence</th>
                  <th className="px-6 py-4 font-medium text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {summary.recent_cases.slice(0, 5).map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-700">{c.customer_name || "Unknown Customer"}</div>
                      <Link href={`/cases/${c.id}`} className="text-[10px] font-mono text-slate-400 group-hover:text-indigo-600 transition-colors">
                        {c.id.split("-")[0]}...
                      </Link>
                      {c.subscription_id && (
                        <div className="mt-1">
                          <span className="rounded px-1.5 py-0.5 text-[9px] font-mono font-bold bg-amber-50 text-amber-600 border border-amber-200">
                            SUB {c.provider_state === 'halted' ? 'HALTED' : 'FAILED'}
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-700">
                      {formatINR(c.amount_at_risk_paise)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-200 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-indigo-500 h-full rounded-full"
                            style={{ width: `${Math.min(c.recovery_probability * 100, 100)}%` }}
                          />
                        </div>
                        <span className="text-[11px] font-medium text-slate-500">
                          {Math.round(c.recovery_probability * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <StatusBadge status={c.status} />
                    </td>
                  </tr>
                ))}
                {summary.recent_cases.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-6 py-12 text-center text-slate-400 text-sm">
                      No active cases in the queue.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Recovery Activity */}
        <div className="lg:col-span-1 rounded-xl border border-slate-200 bg-white flex flex-col overflow-hidden">
          <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-4 bg-slate-50/50">
            <Clock className="h-4 w-4 text-slate-400" />
            <h2 className="text-sm font-semibold text-slate-900">Live Activity</h2>
          </div>
          <div className="p-6 flex-1 overflow-y-auto">
            <div className="space-y-6 relative before:absolute before:inset-0 before:ml-2.5 before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-slate-200 before:to-transparent">
              {summary.recent_cases.slice(0, 5).map((c, idx) => {
                const isRecovered = c.status === "RECOVERED";
                const isBlocked = c.status === "BLOCKED";
                
                let Icon = Zap;
                let bgClass = "bg-indigo-50 border-indigo-200 text-indigo-600";
                
                if (isRecovered) {
                  Icon = CheckCircle2;
                  bgClass = "bg-emerald-50 border-emerald-200 text-emerald-600";
                } else if (isBlocked) {
                  Icon = Ban;
                  bgClass = "bg-rose-50 border-rose-200 text-rose-600";
                }

                return (
                  <div key={idx} className="relative flex items-start gap-4">
                    <div className={`flex items-center justify-center w-6 h-6 rounded-full border shadow-sm shrink-0 relative z-10 mt-0.5 ${bgClass}`}>
                       <Icon className={`h-3 w-3`} />
                    </div>
                    <div className="flex-1 pt-0.5">
                       <div className="text-xs text-slate-700 font-medium">
                         {isRecovered ? (
                           <span>Recovered <span className="text-emerald-600">{formatINR(c.amount_recovered_paise || c.amount_at_risk_paise)}</span></span>
                         ) : isBlocked ? (
                           <span>Policy blocked recovery</span>
                         ) : (
                           <span>Analyzed <span className="text-indigo-600">{formatINR(c.amount_at_risk_paise)}</span> risk</span>
                         )}
                       </div>
                       <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-2">
                         <span className="truncate max-w-[120px]">{c.customer_name || "Unknown"}</span>
                         <span className="w-1 h-1 rounded-full bg-slate-300"></span>
                         <span className="font-mono">{c.id.split("-")[0]}</span>
                       </div>
                    </div>
                  </div>
                )
              })}
              {summary.recent_cases.length === 0 && (
                <div className="text-xs text-slate-400 text-center py-4">No recent activity</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
