"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Play, ShieldAlert, X, AlertCircle, Link as LinkIcon, CheckCircle2 } from "lucide-react";
import { API_BASE } from "@/lib/config";

interface CaseActionsProps {
  caseId: string;
  status: string;
  eventType?: string;
  actualAction?: string;
}

export default function CaseActions({ caseId, status, eventType, actualAction }: CaseActionsProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  const handleSimulateWebhook = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/webhooks/razorpay/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId }),
      });
      if (!res.ok) {
        let errorMsg = "Failed to dispatch simulation webhook";
        try {
            const data = await res.json();
            errorMsg = data.detail || data.message || errorMsg;
        } catch(e) {}
        throw new Error(errorMsg);
      }
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Webhook error");
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

        {/* Phase 4: Simulate Customer Payment Webhook when WAITING_RESULT */}
        {status === "WAITING_RESULT" && (
          <button
            onClick={handleSimulateWebhook}
            disabled={loading}
            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition-colors shadow-lg shadow-emerald-600/25 disabled:opacity-50 animate-pulse"
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            {loading ? "Processing Webhook..." : "Simulate Customer Payment (Webhook)"}
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
    </div>
  );
}
