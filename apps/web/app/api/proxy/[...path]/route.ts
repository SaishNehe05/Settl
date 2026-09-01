import { NextRequest, NextResponse } from "next/server";

async function proxyHandler(req: NextRequest, props: { params: Promise<{ path: string[] }> }) {
  const params = await props.params;
  const targetPath = params.path.join("/");
  
  let backendUrl = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  if (backendUrl.includes("localhost")) {
    backendUrl = backendUrl.replace("localhost", "127.0.0.1");
  }

  // Preserve query string
  const searchParams = req.nextUrl.searchParams.toString();
  const url = searchParams
    ? `${backendUrl}/${targetPath}?${searchParams}`
    : `${backendUrl}/${targetPath}`;

  try {
    const headers = new Headers();
    const contentType = req.headers.get("Content-Type");
    if (contentType) headers.set("Content-Type", contentType);
    
    // Forward auth header
    const authHeader = req.headers.get("Authorization");
    if (authHeader) {
      headers.set("Authorization", authHeader);
    }

    const fetchOptions: RequestInit = {
      method: req.method,
      headers,
    };

    // Only include body for methods that support it
    if (req.method !== "GET" && req.method !== "HEAD") {
      const body = await req.text();
      if (body) fetchOptions.body = body;
    }

    const response = await fetch(url, fetchOptions);
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

export async function GET(req: NextRequest, props: { params: Promise<{ path: string[] }> }) { return proxyHandler(req, props); }
export async function POST(req: NextRequest, props: { params: Promise<{ path: string[] }> }) { return proxyHandler(req, props); }
export async function PATCH(req: NextRequest, props: { params: Promise<{ path: string[] }> }) { return proxyHandler(req, props); }
export async function PUT(req: NextRequest, props: { params: Promise<{ path: string[] }> }) { return proxyHandler(req, props); }
export async function DELETE(req: NextRequest, props: { params: Promise<{ path: string[] }> }) { return proxyHandler(req, props); }

