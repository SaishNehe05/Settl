import { DashboardSummary, RecoveryCaseItem, RecoveryCaseDetail, Policy } from "@/types/api";
import { cookies } from "next/headers";

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
    
  let token = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("settl_token");
  } else {
    try {
      const cookieStore = await cookies();
      token = cookieStore.get("settl_token")?.value;
    } catch (e) {
      // Ignore errors when cookies() is called outside of request context (e.g., build time)
    }
  }

  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(url, { cache: "no-store", headers });
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
    
  let token = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("settl_token");
  } else {
    try {
      const cookieStore = await cookies();
      token = cookieStore.get("settl_token")?.value;
    } catch (e) {}
  }

  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(url, { cache: "no-store", headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Cases Fetch Failed (${res.status}): ${text.substring(0, 100)}`);
  }
  return await res.json();
}

export async function fetchCaseDetail(id: string): Promise<RecoveryCaseDetail | null> {
  let token = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("settl_token");
  } else {
    try {
      const cookieStore = await cookies();
      token = cookieStore.get("settl_token")?.value;
    } catch (e) {}
  }

  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  try {
    const res = await fetch(`${API_BASE}/api/v1/recovery-cases/${encodeURIComponent(id)}`, {
      cache: "no-store",
      headers,
    });
    if (!res.ok) throw new Error(`Failed to fetch case ${id}`);
    return await res.json();
  } catch (err) {
    console.error(`Failed to fetch case ${id}:`, err);
    return null;
  }
}

export async function fetchPolicy(): Promise<Policy> {
  let token = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("settl_token");
  } else {
    try {
      const cookieStore = await cookies();
      token = cookieStore.get("settl_token")?.value;
    } catch (e) {}
  }

  const headers = new Headers();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}/api/v1/policies`, { cache: "no-store", headers });
  if (!res.ok) throw new Error("Failed to fetch policy");
  return await res.json();
}

export async function updatePolicy(policy: Partial<Policy>): Promise<Policy> {
  let token = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("settl_token");
  } else {
    try {
      const cookieStore = await cookies();
      token = cookieStore.get("settl_token")?.value;
    } catch (e) {}
  }

  const headers = new Headers();
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}/api/v1/policies`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(policy),
  });
  if (!res.ok) throw new Error("Failed to update policy");
  return await res.json();
}
