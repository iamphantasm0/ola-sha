import { OrderState } from "../../lib/types";
import { ReceiptCard } from "./ReceiptCard";

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div className="flex justify-between gap-2 py-1 text-xs">
      <span className="text-gray-500">{label}</span>
      <span className="text-right text-[#e6e8ec] break-all">{value}</span>
    </div>
  );
}

const STATUS_LABEL: Record<string, string> = {
  IDLE: "Idle",
  OFFRAMP_QUOTING: "Quote ready",
  OFFRAMP_COLLECTING_BANK: "Collecting bank details",
  OFFRAMP_AWAITING_DEPOSIT: "Awaiting your deposit",
  OFFRAMP_PROCESSING: "Settling…",
  ONRAMP_QUOTING: "Quote ready",
  ONRAMP_COLLECTING_WALLET: "Collecting wallet",
  ONRAMP_AWAITING_PAYMENT: "Awaiting your payment",
  ONRAMP_PROCESSING: "Settling…",
  SETTLED: "Settled",
  FAILED: "Failed",
  CANCELLED: "Cancelled",
};

export function StatusPanel({ order }: { order: OrderState | null }) {
  return (
    <div className="flex h-full w-full flex-col gap-3 border-l border-edge bg-ink p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-gray-500">
        Transaction
      </div>

      {!order ? (
        <div className="text-xs text-gray-500">No active transaction yet.</div>
      ) : (
        <>
          <div className="rounded-xl border border-edge bg-panel p-3">
            <div className="mb-1 text-sm font-medium text-accent">
              {STATUS_LABEL[order.status] ?? order.status}
            </div>
            <Row label="Direction" value={order.direction} />
            <Row
              label="Amount"
              value={order.amount && order.token ? `${order.amount} ${order.token}` : null}
            />
            <Row label="Currency" value={order.currency} />
            <Row
              label="You receive"
              value={
                order.output_amount && order.currency
                  ? `${order.output_amount.toLocaleString()} ${order.currency}`
                  : null
              }
            />
            <Row label="Paycrest ref" value={order.paycrest_order_id} />
            <Row label="Deposit to" value={order.deposit_address} />
          </div>
          <ReceiptCard order={order} />
        </>
      )}
    </div>
  );
}
