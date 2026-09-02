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
