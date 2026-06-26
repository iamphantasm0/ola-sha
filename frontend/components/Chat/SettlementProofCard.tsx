import Link from "next/link";
import { OrderState, SettlementProof } from "../../lib/types";
import { DownloadReceiptButton } from "../Sidebar/DownloadReceiptButton";

const STORAGE_SCAN = "https://storagescan-galileo.0g.ai/tx";
const CHAIN_SCAN = "https://chainscan-galileo.0g.ai/tx";

function shortHash(h: string) {
  return `${h.slice(0, 14)}…${h.slice(-8)}`;
}

export function SettlementProofCard({
  proof,
  order,
}: {
  proof: SettlementProof;
  order?: OrderState | null;
}) {
  const verifyId = proof.storage_hash ?? proof.registry_tx_hash ?? proof.order_id;

  return (
    <div className="mt-3 rounded-xl border border-gold/25 bg-gold-soft/40 p-3 ring-1 ring-gold/15">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="font-display text-[13px] text-gold">Notarized on 0G</div>
          <p className="mt-1 text-[11px] leading-relaxed text-muted">
            Immutable record on Storage · settlement logged on Chain. The on-chain event embeds the
            storage hash.
          </p>
        </div>
        <div className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-full border border-gold/40 text-center">
          <span className="font-display text-[8px] font-semibold leading-none text-gold">0G</span>
          <span className="text-[6px] uppercase tracking-wider text-gold/70">proof</span>
        </div>
      </div>

      <div className="mt-3 space-y-2">
        {proof.storage_hash && (
          <div>
            <div className="text-[9px] uppercase tracking-[0.12em] text-muted">Storage record</div>
            <a
              href={`${STORAGE_SCAN}/${proof.storage_hash}`}
              target="_blank"
              rel="noreferrer"
              className="font-mono text-[11px] text-text underline decoration-gold/40 hover:decoration-gold"
            >
              {shortHash(proof.storage_hash)}
            </a>
          </div>
        )}
        {proof.registry_tx_hash && (
          <div>
            <div className="text-[9px] uppercase tracking-[0.12em] text-muted">Chain settlement</div>
            <a
              href={`${CHAIN_SCAN}/${proof.registry_tx_hash}`}
              target="_blank"
              rel="noreferrer"
              className="font-mono text-[11px] text-text underline decoration-gold/40 hover:decoration-gold"
            >
              {shortHash(proof.registry_tx_hash)}
            </a>
          </div>
        )}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Link
          href={`/verify?id=${encodeURIComponent(verifyId)}`}
          className="text-[11px] font-medium text-gold hover:text-text"
        >
          Verify live on Ola →
        </Link>
        {order && (
          <DownloadReceiptButton
            order={order}
            className="rounded-full border border-gold/35 px-3 py-1 text-[10px] font-medium text-gold transition-colors hover:bg-gold/10 disabled:opacity-50"
          />
        )}
      </div>
    </div>
  );
}