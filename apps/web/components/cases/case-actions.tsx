"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Play, ShieldAlert, X, AlertCircle, Link as LinkIcon, CalendarDays, X as XIcon } from "lucide-react";
import { API_BASE } from "@/lib/config";
import { RecoveryCaseDetail } from "@/types/api";
import { formatINR } from "@/lib/utils";

interface CaseActionsProps {
  caseDetail: RecoveryCaseDetail;
}

export default function CaseActions({ caseDetail }: CaseActionsProps) {
  const { id: caseId, status, event_type: eventType, actual_action: actualAction } = caseDetail;
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPromiseModal, setShowPromiseModal] = useState(false);
  const [promiseDate, setPromiseDate] = useState("");

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/recovery-cases/${caseId}/evaluate`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Evaluation failed");
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Failed to evaluate case");
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/recovery-cases/${caseId}/execute`, {
        method: "POST",
      });
      if (!res.ok) throw new Error("Failed to generate payment link");
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Execution error");
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (approved: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const action = approved ? "approve" : "reject";
      const res = await fetch(`${API_BASE}/api/v1/recovery-cases/${caseId}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: approved ? "Approved by operator" : "Rejected by operator" }),
      });
      if (!res.ok) throw new Error("Review action failed");
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Failed to submit review");
    } finally {
      setLoading(false);
    }
  };

  const handleRecordPromise = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promiseDate) {
      setError("Please select a date.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/recovery-cases/${caseId}/promise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          amount_paise: caseDetail.invoice_amount_paise || caseDetail.amount_at_risk_paise,
          promise_date: promiseDate,
        }),
      });
      if (!res.ok) throw new Error("Failed to record promise");
      setShowPromiseModal(false);
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Failed to record promise");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      {error && (
        <div className="flex items-center gap-1.5 text-xs text-rose-400 bg-rose-950/40 p-2 rounded border border-rose-900">
          <AlertCircle className="h-3.5 w-3.5" />
          {error}
        </div>
      )}
      <div className="flex flex-wrap items-center gap-2">
        {/* On-demand evaluation button (when not yet approved or recovered) */}
        {!["APPROVED", "WAITING_RESULT", "RECOVERED"].includes(status) && (
          <button
            onClick={handleEvaluate}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:text-white transition-colors disabled:opacity-50"
          >
            <Play className="h-3.5 w-3.5 text-sky-400" />
            {loading ? "Evaluating..." : "Run Policy Check"}
          </button>
        )}

        {/* Phase 4: Execute Recovery Action when APPROVED */}
        {status === "APPROVED" && (
          <button
            onClick={handleExecute}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-sky-500 transition-colors shadow-lg shadow-sky-600/25 disabled:opacity-50"
          >
            {actualAction === "CREATE_PAYMENT_LINK" ? (
              <><LinkIcon className="h-3.5 w-3.5" /> {loading ? "Generating..." : "Create Razorpay Payment Link"}</>
            ) : actualAction === "RECOVER_CHECKOUT" ? (
              <><LinkIcon className="h-3.5 w-3.5" /> {loading ? "Recovering..." : "Recover Checkout"}</>
            ) : actualAction === "SEND_REMINDER" ? (
              <><Play className="h-3.5 w-3.5" /> {loading ? "Sending..." : "Send Reminder"}</>
            ) : actualAction === "MONITOR" || actualAction === "WAIT" ? (
              <><Play className="h-3.5 w-3.5" /> {loading ? "Scheduling..." : "Schedule Monitoring"}</>
            ) : actualAction === "RECORD_PROMISE" ? (
              <><Check className="h-3.5 w-3.5" /> {loading ? "Recording..." : "Record Promise"}</>
            ) : actualAction === "CREATE_COLLECTION_CASE" ? (
              <><ShieldAlert className="h-3.5 w-3.5" /> {loading ? "Creating..." : "Create Collection Case"}</>
            ) : (
              <><Play className="h-3.5 w-3.5" /> {loading ? "Executing..." : "Execute Action"}</>
            )}
          </button>
        )}

        {/* Promise to Pay Button (Always available if case is active and no active promise exists) */}
        {!["RECOVERED", "BLOCKED", "STOPPED"].includes(status) && 
         !caseDetail.promises?.some(p => p.status === "PROMISED") && (
          <button
            onClick={() => setShowPromiseModal(true)}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:text-white transition-colors disabled:opacity-50"
          >
            <Check className="h-3.5 w-3.5 text-sky-400" />
            Record Promise to Pay
          </button>
        )}

        {/* Human Escalation Review Buttons */}
        {status === "ESCALATED" && (
          <>
            <button
              onClick={() => handleReview(true)}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-600/20 disabled:opacity-50"
            >
              <Check className="h-3.5 w-3.5" />
              Approve Recovery
            </button>
            <button
              onClick={() => handleReview(false)}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-1.5 text-xs font-medium text-rose-300 hover:bg-rose-900 transition-colors disabled:opacity-50"
            >
              <X className="h-3.5 w-3.5" />
              Reject & Stop
            </button>
          </>
        )}
      </div>

      {showPromiseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Record Promise to Pay</h3>
              <button onClick={() => setShowPromiseModal(false)} className="text-slate-400 hover:text-white">
                <XIcon className="h-5 w-5" />
              </button>
            </div>
            
            <form onSubmit={handleRecordPromise} className="space-y-4">
              <div className="space-y-3 text-sm text-slate-300 bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="flex justify-between">
                  <span className="text-slate-500">Customer</span>
                  <span className="font-medium text-white">{caseDetail.customer?.name || "Unknown"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Invoice / Reference</span>
                  <span className="font-mono text-white">{caseDetail.external_invoice_id || caseDetail.invoice_id || "N/A"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Amount</span>
                  <span className="font-mono text-sky-400 font-bold">
                    {formatINR(caseDetail.invoice_amount_paise || caseDetail.amount_at_risk_paise)}
                  </span>
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">Promised Date</label>
                <div className="relative">
                  <input
                    type="date"
                    required
                    min={new Date().toISOString().split('T')[0]}
                    value={promiseDate}
                    onChange={(e) => setPromiseDate(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                  />
                </div>
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowPromiseModal(false)}
                  className="flex-1 rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-500 transition-colors shadow-lg shadow-sky-600/25 disabled:opacity-50"
                >
                  {loading ? "Saving..." : "Record Promise"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
