import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET(
  req: NextRequest,
  { params }: { params: { orderId: string } }
) {
  // Forward the caller's session id so the backend can scope the order to its owner.
  const sessionId = req.headers.get("x-session-id") ?? "";
  const res = await fetch(`${BACKEND}/api/v1/orders/${params.orderId}`, {
    cache: "no-store",
    headers: { "x-session-id": sessionId },
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
