export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface OrderState {
  order_id: string;
  status: string;
  direction: string | null;
  amount: number | null;
  token: string | null;
  currency: string | null;
  output_amount: number | null;
  deposit_address: string | null;
  storage_hash: string | null;
  registry_tx_hash: string | null;
  paycrest_order_id: string | null;
}

export interface ChatResponse {
  reply: string;
  order_state: OrderState | null;
  tool_called: string | null;
}

// States where the backend is awaiting an external event — poll for updates.
export const POLLING_STATES = new Set([
  "OFFRAMP_AWAITING_DEPOSIT",
  "OFFRAMP_PROCESSING",
  "ONRAMP_AWAITING_PAYMENT",
  "ONRAMP_PROCESSING",
]);

export const TERMINAL_STATES = new Set(["SETTLED", "FAILED", "CANCELLED"]);
