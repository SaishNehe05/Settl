"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Play, ShieldAlert, X, AlertCircle } from "lucide-react";

interface CaseActionsProps {
  caseId: string;
  status: string;
}

export default function CaseActions({ caseId, status }: CaseActionsProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/recovery-cases/${caseId}/evaluate`, {
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

  const handleReview = async (approved: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const action = approved ? "approve" : "reject";
      const res = await fetch(`http://localhost:8000/api/v1/recovery-cases/${caseId}/${action}`, {
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
        {/* On-demand evaluation button */}
        <button
          onClick={handleEvaluate}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:text-white transition-colors disabled:opacity-50"
        >
          <Play className="h-3.5 w-3.5 text-sky-400" />
          {loading ? "Evaluating..." : "Run Policy Check"}
        </button>

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
