"""
Paycrest v2 webhook handler — where 0G Storage + 0G Chain get called.

Events (webhookVersion "2"):
  payment_order.deposited  -> offramp: stablecoin deposit detected
  payment_order.pending    -> onramp: fiat deposit confirmed by provider
  payment_order.validated  -> offramp: fiat payout confirmed   (notify user)
  payment_order.settling   -> onchain release in progress
  payment_order.settled    -> order complete                   (write 0G records)
  payment_order.refunding / refunded / expired -> failure paths

Paycrest retries with exponential backoff for 24h on any non-2xx, so we always
return 200 once we've accepted the event. Idempotency is enforced by checking
the order's current status before writing 0G records.
"""

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.order import OrderStatus
from app.repositories.orders import OrderRepository
from app.services.registry import log_to_registry
from app.services.status import push_status_update
from app.services.storage import store_transaction_record

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """HMAC-SHA256 over the raw body; compare as lowercase hex strings."""
    sig = (signature or "").strip().lower()
    if not sig:
        return False
    computed = hmac.new(
        secret.strip().encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest().lower()
    if len(computed) != len(sig):
        return False
    return hmac.compare_digest(computed.encode("utf-8"), sig.encode("utf-8"))


@router.post("/webhooks/paycrest")
async def paycrest_webhook(request: Request, db=Depends(get_db)):
    raw_body = await request.body()

    sig = request.headers.get("X-Paycrest-Signature", "")
    if not _verify_signature(raw_body, sig, settings.PAYCREST_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(raw_body)
    event = payload.get("event", "")
    data = payload.get("data", {}) or {}
    paycrest_id = data.get("id", "")
    direction = data.get("direction", "")
    status = data.get("status", "")

    order = await OrderRepository.get_by_paycrest_id(db, paycrest_id)
    if not order:
        return {"ok": True}  # not ours — acknowledge

    if event == "payment_order.validated" and direction == "offramp":
        await OrderRepository.update_status(db, order.id, OrderStatus.OFFRAMP_PROCESSING)
        await push_status_update(
            db,
            order,
            {"event": "validated", "message": "Fiat payment confirmed. Settlement completing on-chain."},
        )

    elif event == "payment_order.pending" and direction == "onramp":
        await OrderRepository.update_status(db, order.id, OrderStatus.ONRAMP_PROCESSING)
        await push_status_update(
            db,
            order,
            {"event": "pending", "message": "Your fiat deposit was received. Sending stablecoin to your wallet."},
        )

    elif event == "payment_order.settled":
        if order.status == OrderStatus.SETTLED:
            return {"ok": True}  # idempotent

        # 1) Immutable audit record -> 0G Storage
        record = {
            "order_id": str(order.id),
            "direction": direction or order.direction,
            "token": order.token,
            "amount": float(order.amount),
            "currency": order.currency,
            "rate": float(order.rate) if order.rate is not None else None,
            "output_amount": float(order.output_amount)
            if order.output_amount is not None
            else None,
            "paycrest_order_id": paycrest_id,
            "tx_hash": data.get("txHash"),
            "event": event,
            "status": status,
            "settled_at": data.get("updatedAt"),
            "product": "Ola — a Sterling Concierge demo by Vela Labs",
            "version": "1.0.0",
        }
        storage_hash = await store_transaction_record(record)

        # 2) Append-only settlement log -> 0G Chain
        order_id_bytes32 = hashlib.sha256(str(order.id).encode("utf-8")).digest()
        chain_tx = await log_to_registry(
            order_id_bytes=order_id_bytes32,
            direction=direction or order.direction,
            currency=order.currency,
            amount_cents=int(float(order.amount) * 100),
            storage_hash=storage_hash,
        )

        # 3) Persist both references
        await OrderRepository.settle(
            db, order.id, storage_hash=storage_hash, registry_tx_hash=chain_tx
        )

        # 4) Surface to the UI
        await push_status_update(
            db,
            order,
            {
                "event": "settled",
                "message": "Transaction complete.",
            },
        )

    elif event in ("payment_order.refunded", "payment_order.expired"):
        await OrderRepository.update_status(db, order.id, OrderStatus.FAILED)
        msg = (
            "Transaction failed. Your funds will be returned."
            if event == "payment_order.refunded"
            else "Transaction expired before payment was received."
        )
        await push_status_update(db, order, {"event": event.split(".")[1], "message": msg})

    return {"ok": True}
