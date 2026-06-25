import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

export async function GET(req: NextRequest) {
  const sessionId = req.nextUrl.searchParams.get("sessionId");
  if (!sessionId) {
    return NextResponse.json({ error: "missing sessionId" }, { status: 400 });
  }
  const backend = process.env.BACKEND_URL || "http://backend:8000";
  const r = await fetch(`${backend}/api/v1/sessions/${sessionId}/order`);
  const data = await r.json();
  return NextResponse.json(data, { status: r.status });
}
