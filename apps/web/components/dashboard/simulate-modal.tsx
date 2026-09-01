"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Zap, AlertTriangle, ShieldX, CheckCircle, X, RefreshCw } from "lucide-react";
import { API_BASE } from "@/lib/api";

const SCENARIOS = [
  {
    id: "payment_degradation",
    name: "Payment Degradation (₹8,499)",
    desc: "UPI/card fails due to transient bank switch error. AI diagnoses root cause and issues automated Payment Link via WhatsApp.",
    icon: Zap,
    color: "text-sky-400",
  },
  {
    id: "checkout_dropoff",
    name: "Checkout Drop-off (₹3,200)",
    desc: "Customer abandons active cart mid-checkout. Agent triggers recovery link with 15-min optimal delay.",
    icon: AlertTriangle,
    color: "text-amber-400",
  },
  {
    id: "subscription_failure",
    name: "Failed Subscription (₹999)",
    desc: "Recurring subscription auto-debit declined. Grace period reminder sent before churn. Max 3 retry policy.",
    icon: RefreshCw,
    color: "text-purple-400",
  },
  {
    id: "b2b_receivables",
    name: "B2B Receivables Chaser (₹75,000)",
    desc: "Overdue B2B invoice exceeds ₹10K autonomous limit. Multi-step email chaser with escalation to senior collections.",
    icon: ShieldX,
    color: "text-emerald-400",
  },
  {
    id: "mandate_retry",
    name: "Mandate Retry Sequencer (₹1,500)",
    desc: "eMandate/NACH auto-debit bounced. Retry scheduled after 24h NPCI-compliant cooldown. Max 2 retries.",
    icon: RefreshCw,
    color: "text-indigo-400",
  },
  {
    id: "hinglish_voice",
    name: "Hinglish Voice Recovery (₹2,499)",
    desc: "Regional customer flagged for IVR outreach. Hinglish voice script delivers 2.3x higher conversion. 9 AM–7 PM IST only.",
    icon: Zap,
    color: "text-teal-400",
  },
  {
    id: "promise_to_pay",
    name: "Promise-to-Pay Tracker (₹4,500)",
    desc: "Customer acknowledged debt and committed to pay. Promise date tracked. Auto-escalate if commitment missed after 48h.",
    icon: CheckCircle,
    color: "text-rose-400",
  },
];

export default function SimulateModal() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [scenario, setScenario] = useState("payment_degradation");
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/events/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario }),
      });
      if (!res.ok) throw new Error("Simulation failed");
      const data = await res.json();
      setOpen(false);
      router.push(`/cases/${data.case.id}`);
      router.refresh();
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="inline-flex items-center gap-2 rounded-lg border border-sky-500/40 bg-sky-950/60 px-3.5 py-2 text-xs font-semibold text-sky-300 hover:bg-sky-900/60 hover:text-white transition-all shadow-sm"
      >
        <Zap className="h-3.5 w-3.5 text-sky-400" />
        Simulate Leakage Event
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20">
                  <Zap className="h-5 w-5 text-sky-400" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Simulate Revenue Leakage Event</h3>
                  <p className="text-xs text-slate-400">
                    Injects a live event to demonstrate autonomous risk analysis & policy rules.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
              {SCENARIOS.map((sc) => {
                const Icon = sc.icon;
                const isSelected = scenario === sc.id;
                return (
                  <div
                    key={sc.id}
                    onClick={() => setScenario(sc.id)}
                    className={`cursor-pointer rounded-xl border p-3.5 transition-all ${
                      isSelected
                        ? "border-sky-500/80 bg-sky-950/40 ring-1 ring-sky-500/30"
                        : "border-slate-800 bg-slate-950/60 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-2 font-medium text-xs text-slate-200">
                      <Icon className={`h-4 w-4 ${sc.color}`} />
                      {sc.name}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 pl-6 leading-relaxed">
                      {sc.desc}
                    </p>
                  </div>
                );
              })}
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setOpen(false)}
                className="rounded-lg px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSimulate}
                disabled={loading}
                className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-500 transition-colors shadow-lg shadow-sky-600/20 disabled:opacity-50"
              >
                {loading ? "Ingesting & Analyzing..." : "Ingest Event & Run Engine"}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
