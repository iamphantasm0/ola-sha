import Link from "next/link";
import { OrderState } from "../../lib/types";
import { DownloadReceiptButton } from "./DownloadReceiptButton";

// Storage value is a 0G Storage Merkle ROOT (content address), not a tx hash — no explorer
// resolves it, so it links to Ola's /verify (live retrieval + decode). Chain tx -> chainscan.
const CHAIN_SCAN = "https://chainscan-galileo.0g.ai/tx";

function HashRow({
  label,
  value,
  href,
  internal = false,
}: {
  label: string;
  value: string;
  href: string;
  internal?: boolean;
}) {
  const cls =
    "block break-all font-mono text-[11px] text-paper-ink underline decoration-gold/40 underline-offset-2 hover:decoration-gold";
  const text = `${value.slice(0, 22)}…${value.slice(-6)}`;
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.12em] text-paper-muted">{label}</div>
      {internal ? (
        <Link href={href} className={cls}>
          {text}
        </Link>
      ) : (
        <a href={href} target="_blank" rel="noreferrer" className={cls}>
          {text}
        </a>
      )}
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
          <HashRow
            label="0G Storage record"
            value={order.storage_hash}
            href={`/verify?id=${encodeURIComponent(order.storage_hash)}`}
            internal
          />
        )}
        {order.registry_tx_hash && (
          <HashRow label="0G Chain settlement" value={order.registry_tx_hash} href={`${CHAIN_SCAN}/${order.registry_tx_hash}`} />
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-3">
        {(order.storage_hash || order.registry_tx_hash) && (
          <Link
            href={`/verify?id=${encodeURIComponent(order.storage_hash ?? order.registry_tx_hash ?? "")}`}
            className="text-[11px] text-paper-ink underline decoration-gold/40 underline-offset-2 hover:decoration-gold"
          >
            Verify live on Ola →
          </Link>
        )}
        <DownloadReceiptButton order={order} />
      </div>
    </div>
  );
}
