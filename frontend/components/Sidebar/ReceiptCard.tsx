import { OrderState } from "../../lib/types";

const STORAGE_SCAN = "https://storagescan-galileo.0g.ai/tx";
const CHAIN_SCAN = "https://chainscan-galileo.0g.ai/tx";

function HashRow({ label, value, href }: { label: string; value: string; href: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.12em] text-paper-muted">{label}</div>
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="block break-all font-mono text-[11px] text-paper-ink underline decoration-gold/40 underline-offset-2 hover:decoration-gold"
      >
        {value.slice(0, 22)}…{value.slice(-6)}
      </a>
    </div>
  );
}

export function ReceiptCard({ order }: { order: OrderState }) {
  if (order.status !== "SETTLED") return null;

  return (
    <div className="relative mt-4 rounded-xl border border-dashed border-paper-ink/25 bg-paper-ink/[0.02] p-4">
      {/* notarized seal — the signature moment */}
      <div className="animate-stampIn seal absolute -right-1 -top-3 flex h-16 w-16 -rotate-12 flex-col items-center justify-center bg-paper text-center">
        <span className="font-display text-[9px] font-semibold leading-none">VERIFIED</span>
        <span className="font-display text-base font-semibold leading-tight">0G</span>
        <span className="text-[7px] uppercase tracking-[0.1em] leading-none">on-chain</span>
      </div>

      <div className="font-display text-base text-paper-ink">Receipt</div>
      <div className="mb-3 text-[11px] text-paper-muted">
        Settled and notarized on the 0G network.
      </div>

      <div className="space-y-2.5 pr-12">
        {order.storage_hash && (
          <HashRow label="0G Storage record" value={order.storage_hash} href={`${STORAGE_SCAN}/${order.storage_hash}`} />
        )}
        {order.registry_tx_hash && (
          <HashRow label="0G Chain settlement" value={order.registry_tx_hash} href={`${CHAIN_SCAN}/${order.registry_tx_hash}`} />
        )}
      </div>
    </div>
  );
}
