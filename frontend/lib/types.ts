export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface Action {
  type: string;
  label: string;
  payload?: Record<string, any>;
  primary?: boolean;
}

export interface OrderState {
  order_id: string;
  status: string;
  direction: string | null;
  amount: number | null;
  token: string | null;
  currency: string | null;
  output_amount: number | null;
  account_name?: string | null;
  bank_name?: string | null;
  account_number?: string | null;
  deposit_address: string | null;
  storage_hash: string | null;
  registry_tx_hash: string | null;
  paycrest_order_id: string | null;
}

export interface ChatResponse {
  reply: string;
  order_state: OrderState | null;
  actions: Action[];
  tool_called: string | null;
  authenticated: boolean;
}

export interface SavedBank {
  id: string;
  currency: string;
  bank_name: string;
  account_number: string;
  account_name: string;
  label: string | null;
}

export interface SavedWallet {
  id: string;
  address: string;
  network: string;
  label: string | null;
}

export interface Settlement {
  order_id: string;
  direction: string | null;
  amount: number | null;
  token: string | null;
  currency: string | null;
  output_amount: number | null;
  settled_at: string | null;
  storage_hash: string | null;
  registry_tx_hash: string | null;
  storage_url: string | null;
  chain_url: string | null;
  storage_record?: Record<string, any> | null;
  chain?: { verified: boolean; block?: number; contract?: string; events?: number };
  matched_by?: "order_id" | "storage_hash" | "registry_tx_hash" | "paycrest_order_id";
}

export interface VerifyRecentResponse {
  settlements: Settlement[];
  next_cursor: string | null;
  has_more: boolean;
}

// States where the backend is awaiting an external event — poll for updates.
export const POLLING_STATES = new Set([
  "OFFRAMP_AWAITING_DEPOSIT",
  "OFFRAMP_PROCESSING",
  "ONRAMP_AWAITING_PAYMENT",
  "ONRAMP_PROCESSING",
]);

export const TERMINAL_STATES = new Set(["SETTLED", "FAILED", "CANCELLED"]);
