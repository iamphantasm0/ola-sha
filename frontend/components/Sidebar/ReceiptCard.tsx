import { OrderState } from "@/lib/types";

export function ReceiptCard({ order }: { order: OrderState }) {
  return (
    <div className="rounded-lg border border-mint/40 bg-mint/5 p-3">
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-mint">
        0G Receipt
      </div>
      {order.storage_hash && (
        <a
          href={`https://storagescan-galileo.0g.ai/tx/${order.storage_hash}`}
          target="_blank"
          rel="noopener noreferrer"
          className="block break-all text-xs text-gray-200 underline hover:text-mint"
        >
          Storage root: {order.storage_hash}
        </a>
      )}
      {order.registry_tx_hash && (
        <a
          href={`https://chainscan-galileo.0g.ai/tx/${order.registry_tx_hash}`}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 block break-all text-xs text-gray-200 underline hover:text-mint"
        >
          Chain tx: {order.registry_tx_hash}
        </a>
      )}
    </div>
  );
}
