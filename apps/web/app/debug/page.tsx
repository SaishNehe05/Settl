import { API_BASE } from "@/lib/api";

export default async function DebugPage() {
  let fetchResult = "Not attempted";
  let fetchStatus = 0;
  let errorMsg = "None";

  try {
    const res = await fetch(`${API_BASE}/api/v1/dashboard/summary`, { cache: "no-store" });
    fetchStatus = res.status;
    fetchResult = await res.text();
  } catch (err: any) {
    errorMsg = err.message || String(err);
  }

  return (
    <div style={{ padding: 40, fontFamily: "monospace", color: "white", background: "#0f172a", minHeight: "100vh" }}>
      <h1>Vercel API Debugger</h1>
      <div style={{ marginTop: 20 }}>
        <strong>API_BASE Variable (from Next.js):</strong>
        <pre style={{ background: "#1e293b", padding: 10, borderRadius: 5 }}>{API_BASE}</pre>
      </div>
      
      <div style={{ marginTop: 20 }}>
        <strong>Fetch Error (if any):</strong>
        <pre style={{ background: "#450a0a", padding: 10, borderRadius: 5 }}>{errorMsg}</pre>
      </div>

      <div style={{ marginTop: 20 }}>
        <strong>HTTP Status Code:</strong>
        <pre style={{ background: "#1e293b", padding: 10, borderRadius: 5 }}>{fetchStatus}</pre>
      </div>

      <div style={{ marginTop: 20 }}>
        <strong>Raw Fetch Output:</strong>
        <pre style={{ background: "#1e293b", padding: 10, borderRadius: 5, whiteSpace: "pre-wrap", overflowX: "auto" }}>
          {fetchResult}
        </pre>
      </div>
    </div>
  );
}
