import { ChatApiResponse, OrderState } from "./types";

export async function sendChat(
  sessionId: string,
  message: string
): Promise<ChatApiResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, sessionId }),
  });
  if (!res.ok) throw new Error("chat request failed");
  return res.json();
}

export async function fetchOrder(sessionId: string): Promise<OrderState | null> {
  const res = await fetch(`/api/order?sessionId=${encodeURIComponent(sessionId)}`);
  if (!res.ok) return null;
  const data = await res.json();
  return data && data.id ? data : null;
}
