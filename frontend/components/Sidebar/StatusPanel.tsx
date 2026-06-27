import { OrderState } from "../../lib/types";
import { ReceiptCard } from "./ReceiptCard";

const STATUS_LABEL: Record<string, string> = {
  IDLE: "Drafting",
  OFFRAMP_QUOTING: "Quote ready",
  OFFRAMP_COLLECTING_BANK: "Awaiting bank",
  OFFRAMP_CONFIRMING_BANK: "Confirm payout",
  OFFRAMP_AWAITING_DEPOSIT: "Awaiting your deposit",
  OFFRAMP_PROCESSING: "Settling",
  ONRAMP_QUOTING: "Quote ready",
  ONRAMP_COLLECTING_WALLET: "Awaiting wallet",
  ONRAMP_AWAITING_PAYMENT: "Awaiting your payment",
  ONRAMP_PROCESSING: "Settling",
  SETTLED: "Settled",
  FAILED: "Failed",
  CANCELLED: "Cancelled",
};

// The journey, in order, used to draw the progress rail.
const FLOW = [
  ["OFFRAMP_QUOTING", "ONRAMP_QUOTING"],
  ["OFFRAMP_COLLECTING_BANK", "OFFRAMP_CONFIRMING_BANK", "ONRAMP_COLLECTING_WALLET"],
  ["OFFRAMP_AWAITING_DEPOSIT", "ONRAMP_AWAITING_PAYMENT"],
  ["OFFRAMP_PROCESSING", "ONRAMP_PROCESSING"],
  ["SETTLED"],
];
const STEP_NAMES = ["Quote", "Details", "Fund", "Settle", "Receipt"];

function Row({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex items-baseline justify-between gap-3 py-1.5">
      <span className="text-[11px] uppercase tracking-[0.12em] text-paper-muted">{label}</span>
      <span className="text-right font-mono text-[13px] text-paper-ink">{value}</span>
    </div>
  );
}

export function StatusPanel({ order }: { order: OrderState | null }) {
  const activeStep = order
    ? Math.max(0, FLOW.findIndex((states) => states.includes(order.status)))
    : -1;
  const settled = order?.status === "SETTLED";
  const failed = order?.status === "FAILED" || order?.status === "CANCELLED";

  return (
    <div className="paper paper-lines flex h-full flex-col rounded-2xl p-5">
      <div className="flex items-baseline justify-between border-b border-paper-ink/10 pb-3">
        <span className="font-display text-lg text-paper-ink">Statement</span>
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-paper-muted">
          Ola · 0G
        </span>
      </div>

      {!order ? (
        <div className="mt-8 text-sm leading-relaxed text-paper-muted">
          No transaction yet.
          <br />
          Tell Ola what you'd like to do and your statement will appear here.
        </div>
      ) : (
        <>
          <div className="mt-3">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
                settled
                  ? "bg-success/15 text-success"
                  : failed
                  ? "bg-danger/15 text-danger"
                  : "bg-paper-ink/8 text-paper-ink"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${settled ? "bg-success" : failed ? "bg-danger" : "bg-gold"} ${!settled && !failed ? "animate-pulse" : ""}`} />
              {STATUS_LABEL[order.status] ?? order.status}
            </span>
          </div>

          {/* progress rail */}
          {!failed && (
            <div className="mt-4 flex gap-1.5">
              {STEP_NAMES.map((name, i) => (
                <div key={name} className="flex-1">
                  <div className={`h-1 rounded-full ${i <= activeStep ? "bg-gold" : "bg-paper-ink/12"}`} />
                  <div className={`mt-1.5 text-[9px] uppercase tracking-wide ${i <= activeStep ? "text-paper-ink" : "text-paper-muted/60"}`}>
                    {name}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-4 border-t border-paper-ink/10 pt-1">
            {(() => {
              const onramp = order.direction === "onramp";
              const crypto = order.amount && order.token ? `${order.amount} ${order.token}` : null;
              const fiat = order.output_amount && order.currency ? `${order.output_amount.toLocaleString()} ${order.currency}` : null;
              return (
                <>
                  <Row label="Type" value={onramp ? "Buy · cash → crypto" : order.direction === "offramp" ? "Sell · crypto → cash" : null} />
                  <Row label={onramp ? "You receive" : "You sell"} value={crypto} />
                  <Row label={onramp ? "You pay" : "You receive"} value={fiat} />
                </>
              );
            })()}
            <Row label="Beneficiary" value={order.account_name} />
            <Row label="Account" value={order.account_number ? `${order.bank_name ?? ""} ••${order.account_number.slice(-4)}` : null} />
            <Row label="Provider ref" value={order.paycrest_order_id ? `${order.paycrest_order_id.slice(0, 10)}…` : null} />
          </div>

          {order.deposit_address && !settled && (
            <div className="mt-3 rounded-lg border border-paper-ink/12 bg-paper-ink/[0.03] p-2.5">
              <div className="text-[10px] uppercase tracking-[0.12em] text-paper-muted">
                Send {order.token}
                {order.network ? ` on ${order.network.replace("-", " ")}` : ""} to
              </div>
              <div className="mt-0.5 break-all font-mono text-[11px] text-paper-ink">{order.deposit_address}</div>
            </div>
          )}

          <ReceiptCard order={order} />
        </>
      )}
    </div>
  );
}
