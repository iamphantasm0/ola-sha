export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
}

export interface OrderState {
  id: string;
  status: string;
  direction: string | null;
  token: string | null;
  amount: number | null;
  currency: string | null;
  rate: number | null;
  output_amount: number | null;
  paycrest_order_id: string | null;
  deposit_address: string | null;
  valid_until: string | null;
  pay_bank_name: string | null;
  pay_account_number: string | null;
  pay_account_name: string | null;
  pay_amount: string | null;
  storage_hash: string | null;
  registry_tx_hash: string | null;
  last_event: string | null;
  last_event_message: string | null;
}

export interface ChatApiResponse {
  reply: string;
  order_state: OrderState | null;
  tool_called: string | null;
}
