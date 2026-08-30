import Link from "next/link";
import { ArrowRight, Filter, Search } from "lucide-react";
import { fetchRecoveryCases } from "@/lib/api";
import { formatINR, formatPercent, formatDate } from "@/lib/utils";
import StatusBadge from "@/components/cases/status-badge";

interface CasesPageProps {
  searchParams: Promise<{ status?: string }>;
}

export const revalidate = 0;

export default async function CasesPage({ searchParams }: CasesPageProps) {
  const { status } = await searchParams;
  const cases = await fetchRecoveryCases(status);

  const statusFilters = [
    { label: "All Cases", value: "" },
    { label: "Ready", value: "READY" },
    { label: "Escalated", value: "ESCALATED" },
    { label: "Blocked / Stopped", value: "BLOCKED" },
    { label: "Recovered", value: "RECOVERED" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Recovery Queue</h1>
        <p className="text-sm text-slate-400 mt-1">
          Inspect and manage individual revenue-loss recovery units across the pipeline.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {statusFilters.map((tab) => {
            const isSelected = (!status && tab.value === "") || status === tab.value;
            return (
              <Link
                key={tab.value}
                href={tab.value ? `/cases?status=${tab.value}` : "/cases"}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  isSelected
                    ? "bg-sky-500/10 text-sky-400 border border-sky-500/30"
                    : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
                }`}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>
      </div>

      {/* Cases Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 backdrop-blur-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="border-b border-slate-800/80 bg-slate-950/60 text-slate-400">
              <tr>
                <th className="px-6 py-3.5 font-medium">Case ID</th>
                <th className="px-6 py-3.5 font-medium">Customer</th>
                <th className="px-6 py-3.5 font-medium">Amount at Risk</th>
                <th className="px-6 py-3.5 font-medium">Priority</th>
                <th className="px-6 py-3.5 font-medium">Recovery Prob</th>
                <th className="px-6 py-3.5 font-medium">Recommended Action</th>
                <th className="px-6 py-3.5 font-medium">Status</th>
                <th className="px-6 py-3.5 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {cases.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-500">
                    No cases match the selected filter.
                  </td>
                </tr>
              ) : (
                cases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-300">
                      <Link href={`/cases/${c.id}`} className="hover:text-sky-400 hover:underline">
                        {c.id}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-200">{c.customer_name || "Demo Customer"}</div>
                      <div className="text-[11px] text-slate-500">{c.customer_email || "-"}</div>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-100">
                      {formatINR(c.amount_at_risk_paise)}
                    </td>
                    <td className="px-6 py-4">
                      <span className="rounded bg-slate-800/80 px-2 py-0.5 text-[10px] font-medium text-slate-300">
                        {c.priority}
                      </span>
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
                      {c.recommended_action || "ANALYZING"}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/cases/${c.id}`}
                        className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:text-white transition-colors"
                      >
                        Inspect
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
