import { ChatResponse, OrderState } from "./types";

export async function sendChat(message: string, sessionId: string): Promise<ChatResponse> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, sessionId }),
  });
  if (!res.ok) throw new Error(`chat failed: ${res.status}`);
  return res.json();
}

export async function fetchOrder(orderId: string, sessionId: string): Promise<OrderState> {
  const res = await fetch(`/api/order/${orderId}`, {
    headers: { "x-session-id": sessionId },
  });
  if (!res.ok) throw new Error(`order fetch failed: ${res.status}`);
  return res.json();
}
