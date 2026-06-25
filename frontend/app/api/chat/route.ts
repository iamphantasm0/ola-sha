import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const { message, sessionId } = await req.json();
  const backend = process.env.BACKEND_URL || "http://backend:8000";

  const r = await fetch(`${backend}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  const data = await r.json();
  return NextResponse.json(data, { status: r.status });
}
