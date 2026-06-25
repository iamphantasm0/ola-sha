import { OrderState } from "@/lib/types";
import { CurrencyBadge } from "./CurrencyBadge";
import { ReceiptCard } from "./ReceiptCard";

const LABELS: Record<string, string> = {
  IDLE: "Ready",
  OFFRAMP_QUOTING: "Quote ready",
  OFFRAMP_COLLECTING_BANK: "Collecting bank details",
  OFFRAMP_AWAITING_DEPOSIT: "Awaiting your deposit",
  OFFRAMP_PROCESSING: "Settling…",
  ONRAMP_QUOTING: "Quote ready",
  ONRAMP_COLLECTING_WALLET: "Collecting wallet",
  ONRAMP_AWAITING_PAYMENT: "Awaiting your payment",
  ONRAMP_PROCESSING: "Sending crypto…",
  SETTLED: "Settled",
  FAILED: "Failed",
  CANCELLED: "Cancelled",
};

function Row({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="text-muted">{label}</span>
      <span className={`text-right ${mono ? "font-mono text-xs" : ""}`}>{value}</span>
    </div>
  );
}

function Box({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line bg-ink p-3">
      <div className="mb-1 text-xs uppercase tracking-wide text-muted">{title}</div>
      {children}
    </div>
  );
}

export function StatusPanel({ order }: { order: OrderState | null }) {
  if (!order) {
    return (
      <div className="p-4 text-sm text-muted">
        No active transaction. Ask Ola to buy or sell to get started.
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4 text-sm">
      <div>
        <div className="text-xs uppercase tracking-wide text-muted">Status</div>
        <div className="mt-1 font-medium text-mint">
          {LABELS[order.status] ?? order.status}
        </div>
        {order.last_event_message && (
          <div className="mt-1 text-xs text-muted">{order.last_event_message}</div>
        )}
      </div>

      <Row
        label="Direction"
        value={
          order.direction === "onramp"
            ? "Buy (fiat → crypto)"
            : "Sell (crypto → fiat)"
        }
      />
      {order.amount != null && (
        <Row label="Amount" value={`${order.amount} ${order.token ?? ""}`} />
      )}
      {order.currency && (
        <div className="flex items-center justify-between">
          <span className="text-muted">Currency</span>
          <CurrencyBadge code={order.currency} />
        </div>
      )}
      {order.rate != null && <Row label="Rate" value={order.rate.toLocaleString()} />}
      {order.output_amount != null && (
        <Row
          label={order.direction === "onramp" ? "You pay" : "You receive"}
          value={order.output_amount.toLocaleString()}
        />
      )}

      {order.deposit_address && (
        <Box title="Deposit address">
          <code className="block break-all text-xs text-gray-200">
            {order.deposit_address}
          </code>
          {order.valid_until && (
            <div className="mt-1 text-xs text-muted">Valid until {order.valid_until}</div>
          )}
        </Box>
      )}

      {order.pay_bank_name && (
        <Box title="Pay into">
          <div className="text-xs text-gray-200">{order.pay_bank_name}</div>
          <div className="text-xs text-gray-200">
            {order.pay_account_number} · {order.pay_account_name}
          </div>
          {order.pay_amount && (
            <div className="mt-1 text-xs text-mint">
              Send {order.pay_amount} {order.currency}
            </div>
          )}
        </Box>
      )}

      {order.paycrest_order_id && (
        <Row label="Paycrest ref" value={order.paycrest_order_id} mono />
      )}

      {order.status === "SETTLED" && <ReceiptCard order={order} />}
    </div>
  );
}
