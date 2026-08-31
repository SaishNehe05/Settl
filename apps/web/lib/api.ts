import { DashboardSummary, RecoveryCaseItem, RecoveryCaseDetail, Policy } from "@/types/api";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Fallback seed data in case backend server is booting
const FALLBACK_SUMMARY: DashboardSummary = {
  revenue_at_risk_paise: 5419900,
  eligible_revenue_paise: 4349900,
  revenue_recovered_paise: 1250000,
  recovery_attempts_count: 3,
  recovery_rate: 0.2874,
  guardrail_blocks_count: 2,
  human_escalations_count: 1,
  total_cases_count: 5,
  active_cases_count: 3,
  recovered_cases_count: 1,
  recent_cases: [
    {
      id: "CASE_8499_RECOVERABLE",
      merchant_id: "MER_DEMO_01",
      revenue_event_id: "EVT_FAILED_8499",
      amount_at_risk_paise: 849900,
      recovery_probability: 0.87,
      root_cause: "temporary_bank_failure",
      priority: "HIGH",
      recommended_action: "CREATE_PAYMENT_LINK",
      attempt_count: 0,
      status: "READY",
      amount_recovered_paise: 0,
      customer_name: "Ananya Sharma",
      customer_email: "ananya.sharma@example.com",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: "CASE_HIGH_VALUE",
      merchant_id: "MER_DEMO_01",
      revenue_event_id: "EVT_HIGH_VALUE",
      amount_at_risk_paise: 3500000,
      recovery_probability: 0.72,
      root_cause: "gateway_error",
      priority: "URGENT",
      recommended_action: "ESCALATE",
      attempt_count: 0,
      status: "ESCALATED",
      amount_recovered_paise: 0,
      customer_name: "Vikram Patel",
      customer_email: "vikram.patel@example.com",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: "CASE_MAX_ATTEMPTS",
      merchant_id: "MER_DEMO_01",
      revenue_event_id: "EVT_MAX_ATTEMPTS",
      amount_at_risk_paise: 450000,
      recovery_probability: 0.25,
      root_cause: "insufficient_funds",
      priority: "LOW",
      recommended_action: "STOP",
      attempt_count: 2,
      status: "BLOCKED",
      amount_recovered_paise: 0,
      customer_name: "Rohan Verma",
      customer_email: "rohan.verma@example.com",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ],
};

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/dashboard/summary`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch dashboard summary");
    return await res.json();
  } catch (err) {
    console.warn("Backend unavailable, using initial cached summary data:", err);
    return FALLBACK_SUMMARY;
  }
}

export async function fetchRecoveryCases(status?: string): Promise<RecoveryCaseItem[]> {
  try {
    const url = status 
      ? `${API_BASE}/api/v1/recovery-cases?status=${encodeURIComponent(status)}`
      : `${API_BASE}/api/v1/recovery-cases`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch recovery cases");
    return await res.json();
  } catch (err) {
    console.warn("Backend unavailable, using initial cached case items:", err);
    return FALLBACK_SUMMARY.recent_cases;
  }
}

export async function fetchCaseDetail(id: string): Promise<RecoveryCaseDetail | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/recovery-cases/${encodeURIComponent(id)}`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`Failed to fetch case ${id}`);
    return await res.json();
  } catch (err) {
    console.warn(`Backend unavailable for case ${id}, generating preview detail:`, err);
    const item = FALLBACK_SUMMARY.recent_cases.find((c) => c.id === id) || FALLBACK_SUMMARY.recent_cases[0];
    return {
      ...item,
      customer: {
        id: "CUS_PREVIEW",
        name: item.customer_name || "Demo Customer",
        email: item.customer_email || "demo@example.com",
        phone: "+919876543210",
        success_rate: 0.92,
        customer_value: "HIGH",
        opted_out: false,
      },
      actions: [],
      audit_logs: [
        {
          id: "AUD_01",
          actor: "SYSTEM",
          event_name: "EVENT_INGESTED",
          reason: `Normalized payment event for ${item.customer_name}`,
          created_at: item.created_at,
        },
        {
          id: "AUD_02",
          actor: "AGENT",
          event_name: "RISK_EVALUATED",
          reason: `Assessed recovery probability: ${item.recovery_probability * 100}%`,
          created_at: item.created_at,
        },
      ],
    };
  }
}

export async function fetchPolicy(): Promise<Policy> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/policies`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch policy");
    return await res.json();
  } catch (err) {
    return {
      id: "POL_DEMO_01",
      merchant_id: "MER_DEMO_01",
      max_attempts: 2,
      max_automated_amount_paise: 1000000,
      min_probability: 0.40,
      cooldown_minutes: 240,
      human_review_above_paise: 1000000,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }
}

export async function updatePolicy(policy: Partial<Policy>): Promise<Policy> {
  const res = await fetch(`${API_BASE}/api/v1/policies`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(policy),
  });
  if (!res.ok) throw new Error("Failed to update policy");
  return await res.json();
}
