import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest, props: { params: Promise<{ path: string[] }> }) {
  const params = await props.params;
  // Reconstruct the path, e.g., ["api", "v1", "events"] -> "api/v1/events"
  const targetPath = params.path.join("/");
  
  let backendUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  if (backendUrl.includes("localhost")) {
    backendUrl = backendUrl.replace("localhost", "127.0.0.1");
  }

  const url = `${backendUrl}/${targetPath}`;

  try {
    const body = await req.text();
    
    const headers = new Headers();
    headers.set("Content-Type", req.headers.get("Content-Type") || "application/json");

    const response = await fetch(url, {
      method: "POST",
      headers,
      body: body || undefined,
    });

    const data = await response.text();

    return new NextResponse(data, {
      status: response.status,
      headers: {
        "Content-Type": response.headers.get("Content-Type") || "application/json",
      },
    });
  } catch (error: any) {
    console.error("Proxy error:", error);
    return NextResponse.json({ error: "Failed to proxy request" }, { status: 500 });
  }
}
