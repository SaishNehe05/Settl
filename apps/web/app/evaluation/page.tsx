"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  CheckCircle2,
  Database,
  Shield,
  Zap,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  ArrowUpRight,
  ShieldAlert,
} from "lucide-react";
import { EvaluationSummary } from "@/types/api";

function formatCurrency(inr: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(inr);
}

function formatPercent(val: number): string {
  return `${(val * 100).toFixed(1)}%`;
}

export default function EvaluationPage() {
  const [data, setData] = useState<EvaluationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [datasetType, setDatasetType] = useState<"locked_test" | "dev">("locked_test");
  const [error, setError] = useState<string | null>(null);

  const fetchBenchmark = async (type: "locked_test" | "dev") => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`http://localhost:8000/api/v1/evaluation/summary?dataset_type=${type}`);
      if (!res.ok) throw new Error("Failed to load evaluation data");
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || "Failed to load benchmark");
    } finally {
      setLoading(false);
    }
  };

  const handleRunBenchmark = async () => {
    try {
      setRunning(true);
      setError(null);
      const res = await fetch("http://localhost:8000/api/v1/evaluation/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_type: datasetType }),
      });
      if (!res.ok) throw new Error("Failed to run benchmark");
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || "Error running benchmark");
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    fetchBenchmark(datasetType);
  }, [datasetType]);

  const settl = data?.strategies?.settl_ai_agent;
  const naive = data?.strategies?.naive_rule_based;
  const noAction = data?.strategies?.no_action;
  const lift = data?.lift;

  return (
    <div className="space-y-8 max-w-6xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <BarChart3 className="h-6 w-6 text-sky-400" />
            Batch Evaluation & Benchmark Harness
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Empirical verification of AI decisions, calibration, and deterministic guardrail integrity across 5,000 synthetic events.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={datasetType}
            onChange={(e) => setDatasetType(e.target.value as any)}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="locked_test">1,000 Locked Test Set</option>
            <option value="dev">4,000 Dev Training Set</option>
          </select>

          <button
            onClick={handleRunBenchmark}
            disabled={running || loading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 transition-colors shadow-lg shadow-sky-600/20 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${running ? "animate-spin" : ""}`} />
            {running ? "Simulating..." : "Re-Run Benchmark"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-800 bg-rose-950/40 p-4 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Strict Separation Callout */}
      <div className="rounded-xl border border-sky-500/20 bg-sky-950/20 p-5 space-y-2.5">
        <div className="flex items-center gap-2 text-sm font-semibold text-sky-300">
          <Database className="h-4 w-4 text-sky-400" />
          Strict Separation Invariant: Offline Benchmark vs. Live Razorpay Test Mode
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          <strong>Official Razorpay Test Mode Constraint:</strong> Razorpay documents a strict limit of 30 active Payment Links per business account in Test Mode. To protect this limit, Settl evaluates the 5,000-event synthetic dataset completely offline via our deterministic simulation harness with ground-truth latent friction labels. Real Razorpay API links are reserved exclusively for live operator tests.
        </p>
      </div>

      {/* Top Headline KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Net Recovered Revenue */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-2 relative overflow-hidden">
          <div className="text-xs font-medium text-slate-400">Net Recovered Revenue</div>
          <div className="text-2xl font-extrabold text-white font-mono">
            {settl ? formatCurrency(settl.net_recovered_inr) : "—"}
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
            <ArrowUpRight className="h-3.5 w-3.5" />
            <span>+{lift?.net_revenue_lift_pct ?? 0}% vs Naive Retries</span>
          </div>
          <div className="text-[11px] text-slate-500">
            Deducts outreach messaging delivery costs
          </div>
        </div>

        {/* Detection Precision */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-2">
          <div className="text-xs font-medium text-slate-400">Recovery Precision</div>
          <div className="text-2xl font-extrabold text-sky-400 font-mono">
            {settl ? formatPercent(settl.precision) : "—"}
          </div>
          <div className="flex items-center gap-1.5 text-xs text-sky-300 font-medium">
            <span>+{lift?.precision_improvement_pts ?? 0} pts vs Naive Retries</span>
          </div>
          <div className="text-[11px] text-slate-500">
            True recoveries / total outreach attempts
          </div>
        </div>

        {/* Detection Recall */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-2">
          <div className="text-xs font-medium text-slate-400">Recovery Recall</div>
          <div className="text-2xl font-extrabold text-indigo-400 font-mono">
            {settl ? formatPercent(settl.recall) : "—"}
          </div>
          <div className="text-xs text-slate-400">
            {settl?.successful_recoveries} / {((settl?.successful_recoveries ?? 0) + (settl?.missed_opportunities_fn ?? 0))} true cases
          </div>
          <div className="text-[11px] text-slate-500">
            Coverage of all genuinely recoverable leaks
          </div>
        </div>

        {/* False Positives Avoided */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-2">
          <div className="text-xs font-medium text-slate-400">Spam Outreach Prevented</div>
          <div className="text-2xl font-extrabold text-emerald-400 font-mono">
            {lift?.wasted_outreach_reduced_count ?? 0}
          </div>
          <div className="text-xs text-emerald-400 font-medium">
            {formatPercent(lift?.spam_reduction_rate ?? 0)} spam reduction
          </div>
          <div className="text-[11px] text-slate-500">
            Opt-outs & unrecoverables shielded
          </div>
        </div>
      </div>

      {/* Comparative Strategy Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Comparative Strategy Benchmark</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Evaluating 1,000 locked test events across three competing recovery methodologies
            </p>
          </div>
          <span className="rounded-full bg-slate-800 border border-slate-700 px-3 py-1 text-[11px] font-mono text-slate-300">
            N = {data?.total_events ?? 1000} events
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase text-[10px]">
                <th className="py-3 px-3">Metric</th>
                <th className="py-3 px-3 text-sky-400 font-semibold bg-sky-950/20 rounded-t-lg">
                  Settl AI Autonomous Agent
                </th>
                <th className="py-3 px-3">Naive Retries Baseline</th>
                <th className="py-3 px-3">No-Action Baseline</th>
                <th className="py-3 px-3 text-emerald-400">Settl Advantage</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              <tr>
                <td className="py-3 px-3 font-medium text-slate-300">Outreach Precision</td>
                <td className="py-3 px-3 font-mono font-bold text-sky-300 bg-sky-950/10">
                  {settl ? formatPercent(settl.precision) : "—"}
                </td>
                <td className="py-3 px-3 font-mono text-slate-400">
                  {naive ? formatPercent(naive.precision) : "—"}
                </td>
                <td className="py-3 px-3 font-mono text-slate-500">0.0%</td>
                <td className="py-3 px-3 font-semibold text-emerald-400">
                  +{lift?.precision_improvement_pts ?? 0} pts precision
                </td>
              </tr>
              <tr>
                <td className="py-3 px-3 font-medium text-slate-300">Outreach Recall</td>
                <td className="py-3 px-3 font-mono font-bold text-sky-300 bg-sky-950/10">
                  {settl ? formatPercent(settl.recall) : "—"}
                </td>
                <td className="py-3 px-3 font-mono text-slate-400">
                  {naive ? formatPercent(naive.recall) : "—"}
                </td>
                <td className="py-3 px-3 font-mono text-slate-500">0.0%</td>
                <td className="py-3 px-3 text-slate-400">Focused targeting</td>
              </tr>
              <tr>
                <td className="py-3 px-3 font-medium text-slate-300">Wasted Outreach (False Positives)</td>
                <td className="py-3 px-3 font-mono font-bold text-emerald-400 bg-sky-950/10">
                  {settl?.wasted_attempts_fp ?? 0} attempts
                </td>
                <td className="py-3 px-3 font-mono text-rose-400">
                  {naive?.wasted_attempts_fp ?? 0} attempts
                </td>
                <td className="py-3 px-3 font-mono text-slate-500">0</td>
                <td className="py-3 px-3 font-semibold text-emerald-400">
                  -{lift?.wasted_outreach_reduced_count ?? 0} wasted outreach
                </td>
              </tr>
              <tr>
                <td className="py-3 px-3 font-medium text-slate-300">Guardrail Halts & Opt-Outs</td>
                <td className="py-3 px-3 font-mono font-bold text-sky-300 bg-sky-950/10">
                  {settl?.guardrail_blocks ?? 0} blocked
                </td>
                <td className="py-3 px-3 font-mono text-rose-400">0 (Spams all)</td>
                <td className="py-3 px-3 font-mono text-slate-500">—</td>
                <td className="py-3 px-3 font-semibold text-emerald-400">100% consent honored</td>
              </tr>
              <tr>
                <td className="py-3 px-3 font-medium text-slate-300">Gross Revenue Recovered</td>
                <td className="py-3 px-3 font-mono font-bold text-sky-300 bg-sky-950/10">
                  {settl ? formatCurrency(settl.gross_recovered_inr) : "—"}
                </td>
                <td className="py-3 px-3 font-mono text-slate-400">
                  {naive ? formatCurrency(naive.gross_recovered_inr) : "—"}
                </td>
                <td className="py-3 px-3 font-mono text-slate-500">₹0</td>
                <td className="py-3 px-3 text-slate-300">High capture</td>
              </tr>
              <tr>
                <td className="py-3 px-3 font-medium text-slate-300">Outreach Cost Incurred</td>
                <td className="py-3 px-3 font-mono font-bold text-sky-300 bg-sky-950/10">
                  {settl ? `₹${settl.outreach_cost_inr.toFixed(2)}` : "—"}
                </td>
                <td className="py-3 px-3 font-mono text-slate-400">
                  {naive ? `₹${naive.outreach_cost_inr.toFixed(2)}` : "—"}
                </td>
                <td className="py-3 px-3 font-mono text-slate-500">₹0</td>
                <td className="py-3 px-3 text-slate-300">Optimized channel routing</td>
              </tr>
              <tr className="bg-slate-800/40">
                <td className="py-3 px-3 font-bold text-white">Net Recovered Revenue</td>
                <td className="py-3 px-3 font-mono font-extrabold text-emerald-400 bg-sky-950/30 text-sm">
                  {settl ? formatCurrency(settl.net_recovered_inr) : "—"}
                </td>
                <td className="py-3 px-3 font-mono font-bold text-slate-300">
                  {naive ? formatCurrency(naive.net_recovered_inr) : "—"}
                </td>
                <td className="py-3 px-3 font-mono text-slate-500">₹0</td>
                <td className="py-3 px-3 font-bold text-emerald-400">
                  +{lift ? formatCurrency(lift.net_revenue_lift_inr) : "—"} Net Lift
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Grid: Confusion Matrix & Category Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Confusion Matrix Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Shield className="h-4 w-4 text-sky-400" />
            Settl Confusion Matrix (N = 1,000 Locked Test)
          </div>
          <div className="grid grid-cols-2 gap-3 text-center text-xs">
            <div className="rounded-xl bg-emerald-950/30 border border-emerald-800/50 p-4 space-y-1">
              <div className="text-slate-400 font-medium">True Positives (Recovered)</div>
              <div className="text-2xl font-bold text-emerald-400 font-mono">
                {data?.confusion_matrix?.settl?.tp ?? 0}
              </div>
              <div className="text-[10px] text-emerald-300/80">
                Successfully recovered genuine failures
              </div>
            </div>

            <div className="rounded-xl bg-rose-950/20 border border-rose-900/40 p-4 space-y-1">
              <div className="text-slate-400 font-medium">False Positives (Wasted Attempts)</div>
              <div className="text-2xl font-bold text-rose-400 font-mono">
                {data?.confusion_matrix?.settl?.fp ?? 0}
              </div>
              <div className="text-[10px] text-rose-300/80">
                Unrecoverable attempts made
              </div>
            </div>

            <div className="rounded-xl bg-sky-950/30 border border-sky-800/40 p-4 space-y-1">
              <div className="text-slate-400 font-medium">True Negatives (Correct Stops)</div>
              <div className="text-2xl font-bold text-sky-400 font-mono">
                {data?.confusion_matrix?.settl?.tn ?? 0}
              </div>
              <div className="text-[10px] text-sky-300/80">
                Correctly halted by policy guardrails
              </div>
            </div>

            <div className="rounded-xl bg-amber-950/20 border border-amber-900/40 p-4 space-y-1">
              <div className="text-slate-400 font-medium">False Negatives (Missed)</div>
              <div className="text-2xl font-bold text-amber-400 font-mono">
                {data?.confusion_matrix?.settl?.fn ?? 0}
              </div>
              <div className="text-[10px] text-amber-300/80">
                Potentially recoverable leaks missed
              </div>
            </div>
          </div>
        </div>

        {/* Category-Wise Recovery Breakdown */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Zap className="h-4 w-4 text-amber-400" />
            Failure Category Recovery Efficacy
          </div>
          <div className="space-y-3">
            {data?.category_breakdown &&
              Object.entries(data.category_breakdown).map(([cat, stats], i) => {
                const recoveryPct = (stats.settl_recovered / stats.total) * 100;
                return (
                  <div key={i} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-slate-300 text-[11px]">{cat}</span>
                      <span className="font-mono font-semibold text-slate-200">
                        {stats.settl_recovered} / {stats.total} ({recoveryPct.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                      <div
                        className="h-full bg-sky-500 rounded-full transition-all"
                        style={{ width: `${recoveryPct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      </div>
    </div>
  );
}
