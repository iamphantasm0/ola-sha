import { OrderState } from "../../lib/types";

const STORAGE_SCAN = "https://storagescan-galileo.0g.ai";
const CHAIN_SCAN = "https://chainscan-galileo.0g.ai/tx";

export function ReceiptCard({ order }: { order: OrderState }) {
  if (order.status !== "SETTLED") return null;
  return (
    <div className="rounded-xl border border-accent/40 bg-accent/5 p-3 text-xs">
      <div className="mb-2 font-medium text-accent">Settled — verifiable on 0G</div>

      {order.storage_hash && (
        <div className="mb-2">
          <div className="text-gray-500">0G Storage root hash</div>
          <a
            href={`${STORAGE_SCAN}/${order.storage_hash}`}
            target="_blank"
            rel="noreferrer"
            className="break-all text-accent underline"
          >
            {order.storage_hash}
          </a>
        </div>
      )}

      {order.registry_tx_hash && (
        <div>
          <div className="text-gray-500">0G Chain registry tx</div>
          <a
            href={`${CHAIN_SCAN}/${order.registry_tx_hash}`}
            target="_blank"
            rel="noreferrer"
            className="break-all text-accent underline"
          >
            {order.registry_tx_hash}
          </a>
        </div>
      )}
    </div>
  );
}
