"use client";

import { useState, useEffect } from "react";
import { formatINR } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { authFetch } from "@/lib/auth";
import { FlaskConical, Play, CheckCircle2, ShieldAlert, Zap, AlertTriangle, ShieldCheck, FileText, Settings2, Activity, PlayCircle, Ban } from "lucide-react";

export default function EvaluationDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const fetchLatest = async () => {
    try {
      const res = await authFetch(`${API_BASE}/api/v1/evaluation/latest`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
        if (json.status === "RUNNING") {
          setRunning(true);
          setTimeout(fetchLatest, 3000);
        } else {
          setRunning(false);
          setLoading(false);
        }
      } else {
        if (res.status === 404) {
          setLoading(false);
        } else {
          throw new Error("Failed to fetch evaluation data");
        }
      }
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatest();
  }, []);

  const runEvaluation = async () => {
    setRunning(true);
    setLoading(true);
    setError("");
    try {
      const res = await authFetch(`${API_BASE}/api/v1/evaluation/run`, { method: "POST" });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Failed to trigger evaluation run");
      }
      setTimeout(fetchLatest, 2000);
    } catch (err: any) {
      setError(err.message);
      setRunning(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12 animate-in fade-in duration-500">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5 mb-2">
            <FlaskConical className="h-6 w-6 text-violet-500" />
            Recovery Intelligence
          </h1>
          <p className="text-sm text-slate-500 max-w-2xl leading-relaxed">
            Automated backtesting of Settl&apos;s decision models and deterministic policy engine against your historical data.
          </p>
        </div>
        <button
          onClick={runEvaluation}
          disabled={running}
          className="bg-violet-600 text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-violet-500 disabled:opacity-50 transition-colors shadow-sm flex items-center gap-2 shrink-0"
        >
          {running ? (
            <>
              <div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
              <span>Evaluating Batch...</span>
            </>
          ) : (
            <>
              <PlayCircle className="h-4 w-4" />
              <span>Run Live Evaluation</span>
            </>
          )}
        </button>
      </div>

      <div className="bg-violet-50 border border-violet-200 p-5 rounded-xl flex items-start gap-4">
        <AlertTriangle className="w-6 h-6 mt-0.5 text-violet-500 shrink-0" />
        <div>
          <h3 className="font-bold text-violet-700 uppercase tracking-widest text-xs mb-1">Evaluation Environment</h3>
          <p className="text-sm text-violet-600/80 leading-relaxed">
            This dashboard simulates the latest AI models and guardrail policies against your historical database cases in a sandboxed execution environment. <strong>No real customers are contacted and no Razorpay links are created during this run.</strong> The revenue metrics shown represent theoretical recovery yield.
          </p>
        </div>
      </div>

      {loading && !data && (
        <div className="flex flex-col items-center justify-center py-24 text-slate-400">
          <div className="h-8 w-8 rounded-full border-4 border-slate-200 border-t-violet-500 animate-spin mb-4" />
          <div className="text-sm font-medium">Loading evaluation results...</div>
        </div>
      )}

      {error && (
        <div className="bg-rose-50 text-rose-600 p-4 rounded-xl border border-rose-200 text-sm">
          {error}
        </div>
      )}

      {data && data.metrics && (
        <>
          {/* Top Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col justify-between hover:border-slate-300 hover:shadow-sm transition-all">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Revenue at Risk</div>
              <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{formatINR(data.metrics.revenue_at_risk_paise)}</h2>
              <p className="text-xs text-slate-400 mt-2">Total value of evaluated cases</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col justify-between hover:border-slate-300 hover:shadow-sm transition-all">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Eligible Revenue</div>
              <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{formatINR(data.metrics.eligible_revenue_paise)}</h2>
              <p className="text-xs text-slate-400 mt-2">Cleared policy guardrails</p>
            </div>
            <div className="bg-violet-50 border border-violet-200 rounded-xl p-5 flex flex-col justify-between hover:border-violet-300 hover:shadow-sm transition-all">
              <div className="text-xs font-semibold text-violet-600 uppercase tracking-wider mb-2">Simulated Yield</div>
              <h2 className="text-2xl font-bold text-violet-700 tracking-tight">{formatINR(data.metrics.recovered_revenue_paise)}</h2>
              <p className="text-xs text-violet-500/60 mt-2">Expected recovery amount</p>
            </div>
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 flex flex-col justify-between hover:border-emerald-300 hover:shadow-sm transition-all">
              <div className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-2">Recovery Rate</div>
              <h2 className="text-2xl font-bold text-emerald-600 tracking-tight">{(data.metrics.recovery_rate * 100).toFixed(1)}%</h2>
              <p className="text-xs text-emerald-500/60 mt-2">Yield vs Eligible pipeline</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Guardrails Box */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 lg:col-span-1 flex flex-col">
              <div className="flex items-center gap-2 mb-6">
                <ShieldAlert className="h-5 w-5 text-amber-500" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Policy Guardrails</h3>
              </div>
              
              <div className="grid grid-cols-2 gap-3 mb-6">
                <div className="text-center p-4 bg-slate-50 rounded-lg border border-slate-100">
                  <h4 className="text-2xl font-bold text-slate-700">{data.metrics.policy_violations}</h4>
                  <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-wider font-semibold">Violations</p>
                </div>
                <div className="text-center p-4 bg-slate-50 rounded-lg border border-slate-100">
                  <h4 className="text-2xl font-bold text-slate-700">{data.metrics.unauthorized_actions}</h4>
                  <p className="text-[10px] text-slate-400 mt-1 uppercase tracking-wider font-semibold">Unauthorized</p>
                </div>
              </div>
              
              <div className="mt-auto space-y-3 text-xs font-medium">
                <div className="flex items-center justify-between p-2.5 rounded bg-emerald-50 border border-emerald-100 text-emerald-600">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Action Allowed</span>
                  </div>
                  <span className="font-mono">{data.metrics.allowed_cases}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded bg-rose-50 border border-rose-100 text-rose-600">
                  <div className="flex items-center gap-2">
                    <Ban className="w-3.5 h-3.5" />
                    <span>Action Stopped</span>
                  </div>
                  <span className="font-mono">{data.metrics.stopped_cases}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded bg-amber-50 border border-amber-100 text-amber-600">
                  <div className="flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5" />
                    <span>Action Escalated</span>
                  </div>
                  <span className="font-mono">{data.metrics.escalated_cases}</span>
                </div>
              </div>
            </div>

            {/* Scenario Breakdown */}
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden lg:col-span-2 flex flex-col">
              <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50">
                <div className="flex items-center gap-2">
                  <Settings2 className="h-5 w-5 text-indigo-500" />
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Scenario Breakdown</h3>
                </div>
              </div>
              <div className="overflow-x-auto flex-1">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-400 uppercase tracking-wider">
                    <tr>
                      <th className="px-6 py-4 font-semibold">Scenario</th>
                      <th className="px-6 py-4 font-semibold text-right">Events</th>
                      <th className="px-6 py-4 font-semibold text-right">At Risk</th>
                      <th className="px-6 py-4 font-semibold text-right">Eligible</th>
                      <th className="px-6 py-4 font-semibold text-right">Recovered</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {Object.entries(data.metrics.scenarios || {}).map(([scenario, stats]: [string, any]) => (
                      <tr key={scenario} className="hover:bg-slate-50 transition-colors">
                        <td className="px-6 py-4 font-medium text-slate-700">
                           {scenario.replace(/_/g, " ")}
                        </td>
                        <td className="px-6 py-4 text-right text-slate-500 font-mono">{stats.cases.toLocaleString()}</td>
                        <td className="px-6 py-4 text-right text-slate-600 font-mono">{formatINR(stats.revenue_at_risk_paise)}</td>
                        <td className="px-6 py-4 text-right text-slate-600 font-mono">{formatINR(stats.eligible_revenue_paise)}</td>
                        <td className="px-6 py-4 text-right font-mono font-medium text-emerald-600">{formatINR(stats.recovered_revenue_paise)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
            <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-violet-500" />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Evaluation Traces</h3>
              </div>
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">Sample of {data.sample_traces.length} cases</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Event ID</th>
                    <th className="px-6 py-4 font-semibold">Amount</th>
                    <th className="px-6 py-4 font-semibold">AI Recommendation</th>
                    <th className="px-6 py-4 font-semibold">Policy Gate</th>
                    <th className="px-6 py-4 font-semibold">Outcome</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.sample_traces.map((t: any) => (
                    <tr key={t.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-6 py-4">
                        <div className="font-mono text-[10px] text-slate-400 mb-1">{t.event_id.split("-")[0]}</div>
                        <div className="text-slate-700">{t.scenario.replace(/_/g, " ")}</div>
                      </td>
                      <td className="px-6 py-4 font-mono text-slate-600">{formatINR(t.amount_paise)}</td>
                      <td className="px-6 py-4 font-mono text-[10px] text-indigo-600 font-semibold">{t.ai_recommendation || "NONE"}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded font-mono text-[9px] font-bold border ${
                          t.policy_decision === 'ALLOW' ? 'bg-emerald-50 text-emerald-600 border-emerald-200' : 
                          t.policy_decision === 'STOP' ? 'bg-rose-50 text-rose-600 border-rose-200' : 
                          'bg-amber-50 text-amber-600 border-amber-200'
                        }`}>
                          {t.policy_decision}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-medium text-slate-600">{t.outcome}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
      
      {!loading && !data && !error && (
        <div className="text-center py-24 text-slate-400 border border-dashed border-slate-200 rounded-xl bg-white">
          <FlaskConical className="w-12 h-12 mx-auto mb-4 opacity-50 text-slate-300" />
          <h3 className="text-sm font-semibold text-slate-600 mb-1">No Evaluation Data</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">Trigger a live data evaluation to backtest the latest models and policies against historical events.</p>
        </div>
      )}
    </div>
  );
}
