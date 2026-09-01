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
