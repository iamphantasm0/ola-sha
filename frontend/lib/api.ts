import { authHeaders } from "./auth";
import { Action, ChatResponse, OrderState, SavedBank, SavedWallet, Settlement } from "./types";

const BASE = "/api/backend";

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}/${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(opts.headers || {}) },
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      detail = (await res.json()).detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

// ─── Auth ─────────────────────────────────────────────────────────────────
export function register(email: string, password: string) {
  return req<{ token: string; email: string; user_id: string }>("auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
export function login(email: string, password: string) {
  return req<{ token: string; email: string; user_id: string }>("auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

// ─── Chat / actions ─────────────────────────────────────────────────────────
export function sendChat(message: string, sessionId: string) {
  return req<ChatResponse>("chat", {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId }),
  });
}
export function sendAction(action: string, sessionId: string, payload: Record<string, any> = {}) {
  return req<ChatResponse>("action", {
    method: "POST",
    body: JSON.stringify({ action, session_id: sessionId, payload }),
  });
}
export function fetchOrder(orderId: string, sessionId: string) {
  return req<OrderState>(`orders/${orderId}`, { headers: { "x-session-id": sessionId } });
}

// ─── Saved accounts ──────────────────────────────────────────────────────────
export function listAccounts() {
  return req<{ bank_accounts: SavedBank[]; wallets: SavedWallet[] }>("accounts");
}
export function addBank(currency: string, bank_name: string, account_number: string) {
  return req<SavedBank>("accounts/bank", {
    method: "POST",
    body: JSON.stringify({ currency, bank_name, account_number }),
  });
}
export function addWallet(address: string, network: string, label?: string) {
  return req<SavedWallet>("accounts/wallet", {
    method: "POST",
    body: JSON.stringify({ address, network, label }),
  });
}

// ─── Public verify ───────────────────────────────────────────────────────────
export function verifyRecent() {
  return req<{ settlements: Settlement[] }>("verify/recent");
}
export function verifyOrder(orderId: string) {
  return req<Settlement>(`verify/order/${orderId}`);
}
