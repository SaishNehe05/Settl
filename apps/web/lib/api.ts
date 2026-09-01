import { DashboardSummary, RecoveryCaseItem, RecoveryCaseDetail, Policy } from "@/types/api";

let apiBase = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

if (typeof window !== "undefined") {
  // If we are in the browser, hit our own Next.js server to proxy the request securely!
  apiBase = "/api/proxy";
} else {
  // Server-side (fetching initial dashboard data)
  if (apiBase.includes("localhost") || apiBase.includes("127.0.0.1")) {
    if (process.env.NODE_ENV === "production") {
      console.warn("WARNING: API_BASE is pointing to localhost in PRODUCTION. This will fail on Vercel.");
    }
    apiBase = apiBase.replace("localhost", "127.0.0.1");
  }
}

export const API_BASE = apiBase;

export async function fetchDashboardSummary(mode?: string): Promise<DashboardSummary> {
  const url = mode 
    ? `${API_BASE}/api/v1/dashboard/summary?mode=${encodeURIComponent(mode)}`
    : `${API_BASE}/api/v1/dashboard/summary`;
    
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Dashboard Fetch Failed (${res.status}): ${text.substring(0, 100)}`);
  }
  return await res.json();
}

export async function fetchRecoveryCases(status?: string): Promise<RecoveryCaseItem[]> {
  const url = status 
    ? `${API_BASE}/api/v1/recovery-cases?status=${encodeURIComponent(status)}` 
    : `${API_BASE}/api/v1/recovery-cases`;
    
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Cases Fetch Failed (${res.status}): ${text.substring(0, 100)}`);
  }
  return await res.json();
}

export async function fetchCaseDetail(id: string): Promise<RecoveryCaseDetail | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/recovery-cases/${encodeURIComponent(id)}`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`Failed to fetch case ${id}`);
    return await res.json();
  } catch (err) {
    console.error(`Failed to fetch case ${id}:`, err);
    return null;
  }
}

export async function fetchPolicy(): Promise<Policy> {
  const res = await fetch(`${API_BASE}/api/v1/policies`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch policy");
  return await res.json();
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
