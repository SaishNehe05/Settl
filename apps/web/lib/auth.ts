"use client";

const TOKEN_KEY = "settl_token";
const MERCHANT_KEY = "settl_merchant";

export interface MerchantInfo {
  id: string;
  name: string;
  email: string;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getMerchant(): MerchantInfo | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(MERCHANT_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setAuth(token: string, merchant: MerchantInfo): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(MERCHANT_KEY, JSON.stringify(merchant));
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(MERCHANT_KEY);
  if (typeof document !== "undefined") {
    document.cookie = "settl_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  }
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

/**
 * Fetch wrapper that automatically injects the Bearer token.
 * Use this for all authenticated API calls from the client.
 */
export async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(url, { ...options, headers });
}
