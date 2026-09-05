import Link from "next/link";
import { 
  AlertTriangle, 
  ArrowUpRight, 
  CheckCircle2, 
  DollarSign, 
  HelpCircle, 
  Percent, 
  RefreshCw, 
  ShieldAlert, 
  Users, 
  Zap,
  ArrowRight
} from "lucide-react";
import { fetchDashboardSummary, fetchReceivablesStatus } from "@/lib/api";
import { formatINR, formatPercent, formatDate } from "@/lib/utils";
import StatusBadge from "@/components/cases/status-badge";
import { MerchantName } from "@/components/auth/merchant-name";

export const revalidate = 0; // Fresh data per request

interface DashboardPageProps {
  searchParams: Promise<{ mode?: string }>;
}

export default async function DashboardPage({ searchParams }: DashboardPageProps) {
  const { mode } = await searchParams;
  const summary = await fetchDashboardSummary(mode);

  const kpis = [
    {
      label: "Revenue at Risk",
      value: formatINR(summary.revenue_at_risk_paise),
      subtext: `${summary.total_cases_count} leakage events detected`,
      icon: AlertTriangle,
      color: "text-rose-400",
      bg: "bg-rose-950/30",
      border: "border-rose-800/40",
    },
    {
      label: "Eligible Revenue",
      value: formatINR(summary.eligible_revenue_paise),
      subtext: "Approved for recovery by policy",
      icon: DollarSign,
      color: "text-sky-400",
      bg: "bg-sky-950/30",
      border: "border-sky-800/40",
    },
    {
      label: "Verified Recovered",
      value: formatINR(summary.revenue_recovered_paise),
      subtext: `${summary.recovered_cases_count} cases verified via webhook`,
      icon: CheckCircle2,
      color: "text-emerald-400",
      bg: "bg-emerald-950/30",
      border: "border-emerald-800/40",
    },
    {
      label: "Recovery Rate",
      value: formatPercent(summary.recovery_rate),
      subtext: "Recovered / Eligible pipeline",
      icon: Percent,
      color: "text-indigo-400",
      bg: "bg-indigo-950/30",
      border: "border-indigo-800/40",
    },
    {
      label: "Guardrail Blocks",
      value: summary.guardrail_blocks_count,
      subtext: "Attempts cap / opt-out honored",
      icon: ShieldAlert,
      color: "text-amber-400",
      bg: "bg-amber-950/30",
      border: "border-amber-800/40",
    },
    {
      label: "Human Escalations",
      value: summary.human_escalations_count,
      subtext: "Above ₹10,000 threshold",
      icon: Users,
      color: "text-purple-400",
      bg: "bg-purple-950/30",
      border: "border-purple-800/40",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            Recovery Command Center
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time autonomous revenue recovery overview for{" "}
            <span className="text-slate-200 font-medium"><MerchantName /></span>.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/cases"
            className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-500 transition-colors shadow-lg shadow-sky-600/20"
          >
            View Recovery Queue
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              className={`rounded-xl border ${kpi.border} ${kpi.bg} p-5 backdrop-blur-sm transition-all hover:translate-y-[-1px]`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">{kpi.label}</span>
                <div className={`rounded-lg p-2 ${kpi.bg} border ${kpi.border}`}>
                  <Icon className={`h-4 w-4 ${kpi.color}`} />
                </div>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold text-white tracking-tight">{kpi.value}</div>
                <div className="text-xs text-slate-400 mt-1">{kpi.subtext}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Primary Recovery Loop Banner */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-sky-400" />
            <h3 className="text-sm font-semibold text-slate-200">The Settl Closed Recovery Loop</h3>
          </div>
          <span className="text-xs text-slate-500">Autonomous Execution Pipeline</span>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2 text-center text-xs">
          <div className="rounded-lg bg-slate-950/80 border border-slate-800/80 p-2.5">
            <div className="font-semibold text-rose-400">1. FAILED</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Webhook Ingested</div>
          </div>
          <div className="rounded-lg bg-slate-950/80 border border-slate-800/80 p-2.5">
            <div className="font-semibold text-indigo-400">2. RISK & CAUSE</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Probability & Grounding</div>
          </div>
          <div className="rounded-lg bg-slate-950/80 border border-slate-800/80 p-2.5">
            <div className="font-semibold text-purple-400">3. DECISION</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Action Enum Selected</div>
          </div>
          <div className="rounded-lg bg-slate-950/80 border border-slate-800/80 p-2.5">
            <div className="font-semibold text-sky-400">4. POLICY GATE</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Deterministic Guardrails</div>
          </div>
          <div className="rounded-lg bg-slate-950/80 border border-slate-800/80 p-2.5">
            <div className="font-semibold text-emerald-400">5. RAZORPAY</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Payment Link Created</div>
          </div>
          <div className="rounded-lg bg-slate-950/80 border border-slate-800/80 p-2.5">
            <div className="font-semibold text-teal-400">6. VERIFIED</div>
            <div className="text-[11px] text-slate-400 mt-0.5">Webhook Reconciled</div>
          </div>
        </div>
      </div>

      {/* Active Recovery Pipeline Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
          <div>
            <h2 className="text-base font-semibold text-white">Active Recovery Pipeline</h2>
            <p className="text-xs text-slate-400 mt-0.5">Latest revenue events requiring autonomous or human follow-up.</p>
          </div>
          <Link
            href="/cases"
            className="flex items-center gap-1 text-xs font-medium text-sky-400 hover:text-sky-300 transition-colors"
          >
            View all {summary.total_cases_count} cases
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800/80 bg-slate-950/60 text-slate-400">
              <tr>
                <th className="px-6 py-3 font-medium">Case ID</th>
                <th className="px-6 py-3 font-medium">Customer</th>
                <th className="px-6 py-3 font-medium">Amount at Risk</th>
                <th className="px-6 py-3 font-medium">Recovery Prob</th>
                <th className="px-6 py-3 font-medium">Recommended Action</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {summary.recent_cases.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-mono font-medium text-slate-300">
                    <Link href={`/cases/${c.id}`} className="hover:text-sky-400 hover:underline">
                      {c.id}
                    </Link>
                    <div className="mt-1 flex flex-col gap-1 items-start">
                      <span className={`rounded px-1.5 py-0.5 text-[9px] font-mono font-bold border ${c.source === 'synthetic' || c.source === 'simulation' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' : 'bg-sky-500/10 text-sky-400 border-sky-500/20'}`}>
                        {c.source === 'synthetic' || c.source === 'simulation' ? (c.source).toUpperCase() : 'RAZORPAY TEST MODE'}
                      </span>
                      {c.subscription_id && (
                        <span className="rounded px-1.5 py-0.5 text-[9px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          SUBSCRIPTION {c.provider_state === 'halted' ? 'HALTED' : 'FAILED'}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-medium text-slate-200">{c.customer_name || "Not available"}</div>
                    <div className="text-[11px] text-slate-500">{c.customer_email || "Not available"}</div>
                  </td>
                  <td className="px-6 py-4 font-semibold text-slate-100">
                    {formatINR(c.amount_at_risk_paise)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-12 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-sky-500 h-full rounded-full"
                          style={{ width: `${Math.min(c.recovery_probability * 100, 100)}%` }}
                        />
                      </div>
                      <span className="font-medium text-slate-300">
                        {formatPercent(c.recovery_probability)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 font-mono text-[11px] text-slate-300">
                    {c.recommended_action || (c.status === "NEW" || c.status === "ANALYZING" ? "ANALYZING" : "Not yet executed")}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      href={`/cases/${c.id}`}
                      className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800 px-2.5 py-1 text-[11px] font-medium text-slate-200 hover:bg-slate-700 hover:text-white transition-colors"
                    >
                      Inspect
                      <ArrowRight className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
