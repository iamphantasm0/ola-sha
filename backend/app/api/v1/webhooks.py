"""Paycrest v2 webhook handler.

Events (lowercase): payment_order.{deposited,pending,validated,settling,settled,
refunding,refunded,expired}. We notify at validated (offramp) / pending (onramp) and
write 0G records at settled.

Note: Ola needs its own Paycrest sender account to receive these (one webhook URL per
account). Until then, the polling reconciler (app/services/reconciler.py) drives the
exact same settlement logic by pulling GET /sender/orders/:id — so the app works with
or without the webhook. Both paths funnel through app/services/settlement.py.

The webhook verifies, flips DB state, returns 200 immediately (Paycrest retries for 24h
on non-2xx), then runs the slow 0G writes in a BackgroundTask. The SETTLED idempotency
guard makes retries (and overlap with the poller) safe.
"""

import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models.order import OrderStatus
from app.repositories.orders import OrderRepository
from app.services.notifications import push_status_update
from app.services.settlement import write_0g_records_bg

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    sig = (signature or "").strip().lower()
    if not sig:
        return False
    computed = hmac.new(secret.strip().encode("utf-8"), raw_body, hashlib.sha256).hexdigest().lower()
    if len(computed) != len(sig):
        return False
    return hmac.compare_digest(computed.encode("utf-8"), sig.encode("utf-8"))


@router.post("/webhooks/paycrest")
async def paycrest_webhook(
    request: Request, background: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    raw_body = await request.body()
    sig = request.headers.get("X-Paycrest-Signature", "")
    if not _verify_signature(raw_body, sig, settings.PAYCREST_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(raw_body)
    event = payload.get("event", "")
    data = payload.get("data", {})
    paycrest_id = data.get("id", "")
    direction = data.get("direction", "")

    order = await OrderRepository.get_by_paycrest_id(db, paycrest_id)
    if not order:
        return {"ok": True}  # not our order

    if event == "payment_order.validated" and direction == "offramp":
        await OrderRepository.set_status(db, order, OrderStatus.OFFRAMP_PROCESSING)
        await push_status_update(order.session_id, {
            "event": "validated", "message": "Fiat payment confirmed. Settlement completing onchain.",
        })

    elif event == "payment_order.pending" and direction == "onramp":
        await OrderRepository.set_status(db, order, OrderStatus.ONRAMP_PROCESSING)
        await push_status_update(order.session_id, {
            "event": "pending", "message": "Fiat deposit received. Sending stablecoin to your wallet.",
        })

    elif event == "payment_order.settled":
        if order.status == OrderStatus.SETTLED:
            return {"ok": True}
        # Defer the slow 0G writes; return 200 now.
        background.add_task(write_0g_records_bg, str(order.id), direction, data)

    elif event in ("payment_order.refunded", "payment_order.expired"):
        await OrderRepository.set_status(db, order, OrderStatus.FAILED)
        await push_status_update(order.session_id, {
            "event": event.split(".")[1],
            "message": "Transaction failed. Your funds will be returned."
            if event.endswith("refunded") else "Transaction expired.",
        })

    return {"ok": True}
