"use client";

import { useState, useEffect } from "react";
import { formatINR } from "@/lib/utils";
import { API_BASE } from "@/lib/config";

export default function EvaluationDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const fetchLatest = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/evaluation/latest`);
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
          throw new Error("Failed to fetch");
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
      await fetch(`${API_BASE}/api/v1/evaluation/run`, { method: "POST" });
      setTimeout(fetchLatest, 2000);
    } catch (err: any) {
      setError(err.message);
      setRunning(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Batch Measurement & Safety Evaluation</h1>
          <p className="text-muted-foreground mt-2">
            Automated testing of Settl&apos;s decision and policy engines across your actual historical events.
          </p>
        </div>
        <button
          onClick={runEvaluation}
          disabled={running}
          className="bg-indigo-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-lg hover:shadow-xl flex items-center space-x-2"
        >
          {running ? (
            <>
              <div className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
              <span>Evaluating Batch...</span>
            </>
          ) : (
            <span>Run Live Data Evaluation</span>
          )}
        </button>
      </div>

      <div className="bg-sky-500/10 border border-sky-500/20 text-sky-500 p-4 rounded-lg flex items-start space-x-3">
        <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        <div>
          <h3 className="font-semibold">LIVE DATA EVALUATION MODE</h3>
          <p className="text-sm opacity-90">This dashboard simulates the latest AI models and policies against your real historical database cases in a protected sandbox. No real customers are contacted and no Razorpay links are created during this run.</p>
        </div>
      </div>

      {loading && !data && (
        <div className="flex justify-center py-20">
          <div className="h-8 w-8 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin" />
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 text-red-500 p-4 rounded-lg border border-red-500/20">
          {error}
        </div>
      )}

      {data && data.metrics && (
        <>
          <div className="grid gap-6 md:grid-cols-4">
            <div className="bg-card border rounded-xl p-6 shadow-sm">
              <p className="text-sm font-medium text-muted-foreground">Revenue at Risk</p>
              <h2 className="text-3xl font-bold mt-2">{formatINR(data.metrics.revenue_at_risk_paise)}</h2>
              <p className="text-xs text-muted-foreground mt-1">Total value of evaluated cases</p>
            </div>
            <div className="bg-card border rounded-xl p-6 shadow-sm">
              <p className="text-sm font-medium text-muted-foreground">Eligible Revenue</p>
              <h2 className="text-3xl font-bold mt-2">{formatINR(data.metrics.eligible_revenue_paise)}</h2>
              <p className="text-xs text-muted-foreground mt-1">Cleared policy guardrails</p>
            </div>
            <div className="bg-indigo-900/20 border border-indigo-500/30 rounded-xl p-6 shadow-sm">
              <p className="text-sm font-medium text-indigo-400">Evaluation Recovered Revenue</p>
              <h2 className="text-3xl font-bold mt-2 text-indigo-500">{formatINR(data.metrics.recovered_revenue_paise)}</h2>
              <p className="text-xs text-indigo-400/70 mt-1">Total successfully recovered</p>
            </div>
            <div className="bg-emerald-900/20 border border-emerald-500/30 rounded-xl p-6 shadow-sm">
              <p className="text-sm font-medium text-emerald-400">Recovery Rate</p>
              <h2 className="text-3xl font-bold mt-2 text-emerald-500">{(data.metrics.recovery_rate * 100).toFixed(1)}%</h2>
              <p className="text-xs text-emerald-400/70 mt-1">Of eligible revenue</p>
            </div>
          </div>

          <div className="grid gap-6">

            <div className="bg-card border rounded-xl p-6 shadow-sm">
              <h3 className="text-lg font-semibold mb-4">Safety Guardrails (Policy Engine)</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-secondary/50 rounded-lg">
                  <h4 className="text-3xl font-bold text-emerald-500">{data.metrics.policy_violations}</h4>
                  <p className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Policy Violations</p>
                </div>
                <div className="text-center p-4 bg-secondary/50 rounded-lg">
                  <h4 className="text-3xl font-bold text-emerald-500">{data.metrics.unauthorized_actions}</h4>
                  <p className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Unauthorized Actions</p>
                </div>
                <div className="text-center p-4 bg-secondary/50 rounded-lg">
                  <h4 className="text-3xl font-bold text-emerald-500">{data.metrics.duplicate_actions}</h4>
                  <p className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">Duplicate Links</p>
                </div>
              </div>
              
              <div className="mt-6 flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                  <span>Allowed: {data.metrics.allowed_cases}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span>Stopped: {data.metrics.stopped_cases}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <span>Escalated: {data.metrics.escalated_cases}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-card border rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b bg-muted/20">
              <h3 className="font-semibold">Scenario Breakdown</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-muted/50 text-muted-foreground text-xs uppercase">
                  <tr>
                    <th className="px-6 py-3">Scenario</th>
                    <th className="px-6 py-3">Events</th>
                    <th className="px-6 py-3">At Risk</th>
                    <th className="px-6 py-3">Eligible</th>
                    <th className="px-6 py-3">Recovered</th>
                    <th className="px-6 py-3">Stopped</th>
                    <th className="px-6 py-3">Escalated</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {Object.entries(data.metrics.scenarios || {}).map(([scenario, stats]: [string, any]) => (
                    <tr key={scenario} className="hover:bg-muted/30">
                      <td className="px-6 py-4 font-medium">{scenario}</td>
                      <td className="px-6 py-4">{stats.cases.toLocaleString()}</td>
                      <td className="px-6 py-4">{formatINR(stats.revenue_at_risk_paise)}</td>
                      <td className="px-6 py-4">{formatINR(stats.eligible_revenue_paise)}</td>
                      <td className="px-6 py-4 text-emerald-500 font-medium">{formatINR(stats.recovered_revenue_paise)}</td>
                      <td className="px-6 py-4 text-red-400">{stats.stopped}</td>
                      <td className="px-6 py-4 text-amber-500">{stats.escalated}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-card border rounded-xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b bg-muted/20 flex justify-between items-center">
              <h3 className="font-semibold">Evaluation Traces (Sample)</h3>
              <span className="text-xs text-muted-foreground">Showing {data.sample_traces.length} cases</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-muted/50 text-muted-foreground text-xs uppercase">
                  <tr>
                    <th className="px-6 py-3">Event ID</th>
                    <th className="px-6 py-3">Scenario</th>
                    <th className="px-6 py-3">Amount</th>
                    <th className="px-6 py-3">AI Recommendation</th>
                    <th className="px-6 py-3">Policy Decision</th>
                    <th className="px-6 py-3">Outcome</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data.sample_traces.map((t: any) => (
                    <tr key={t.id} className="hover:bg-muted/30">
                      <td className="px-6 py-4 font-mono text-xs">{t.event_id}</td>
                      <td className="px-6 py-4">{t.scenario}</td>
                      <td className="px-6 py-4">{formatINR(t.amount_paise)}</td>
                      <td className="px-6 py-4 text-xs font-mono">{t.ai_recommendation}</td>
                      <td className="px-6 py-4 text-xs">
                        <span className={`px-2 py-1 rounded-full ${t.policy_decision === 'ALLOW' ? 'bg-emerald-500/10 text-emerald-500' : t.policy_decision === 'STOP' ? 'bg-red-500/10 text-red-500' : 'bg-amber-500/10 text-amber-500'}`}>
                          {t.policy_decision}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-medium">{t.outcome}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
      
      {!loading && !data && !error && (
        <div className="text-center py-20 text-muted-foreground border-2 border-dashed rounded-xl">
          <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 className="text-lg font-medium">No Evaluation Data</h3>
          <p className="mt-1">Click the button above to run the live data evaluation.</p>
        </div>
      )}
    </div>
  );
}
