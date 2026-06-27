import { authHeaders } from "./auth";
import {
  Action,
  ChatResponse,
  OrderHistoryResponse,
  OrderState,
  RegistryStats,
  SavedBank,
  SavedWallet,
  Settlement,
  VerifyRecentResponse,
} from "./types";

const BASE = "/api/backend";

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}/${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(opts.headers || {}) },
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      const raw = body?.detail;
      if (typeof raw === "string") detail = raw;
      else if (Array.isArray(raw)) detail = raw.map((d: { msg?: string }) => d.msg ?? "Invalid request").join(", ");
      else if (raw != null) detail = String(raw);
    } catch {
      /* non-JSON body */
    }
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

export function fetchOrderHistory(cursor?: string, limit = 20) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return req<OrderHistoryResponse>(`orders/history?${params}`);
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

// ─── Public on-chain stats ───────────────────────────────────────────────────
export function fetchRegistryStats() {
  return req<RegistryStats>("stats/registry");
}

// ─── Public verify ───────────────────────────────────────────────────────────
export function verifyRecent(cursor?: string, limit = 8) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) params.set("cursor", cursor);
  return req<VerifyRecentResponse>(`verify/recent?${params}`);
}
export function verifyLookup(id: string) {
  return req<Settlement>(`verify/lookup?q=${encodeURIComponent(id.trim())}`);
}
export function verifyOrder(orderId: string) {
  return req<Settlement>(`verify/order/${orderId}`);
}
