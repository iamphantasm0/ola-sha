"""Polling reconciler — the no-webhook path to detecting settlement.

Paycrest allows one webhook URL per sender account, so until Ola has its own account
we cannot receive webhooks. Instead we PULL each active order's status from
GET /sender/orders/:id and run the identical settlement logic (app/services/settlement).

This runs as a background task started in the app lifespan. It is idempotent and safe
to overlap with the webhook (the SETTLED guard prevents double 0G writes).
"""

import asyncio
import logging

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.providers.base import IFiatProvider
from app.providers.paycrest import PaycrestProvider
from app.repositories.orders import OrderRepository
from app.services.settlement import apply_status

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = int(getattr(settings, "RECONCILE_INTERVAL", 0) or 10)


async def reconcile_order(db, order, provider: IFiatProvider) -> str:
    """Pull one order's live status from Paycrest and apply it. Returns the action."""
    data = await provider.get_order_status(order.paycrest_order_id)
    return await apply_status(db, order, data)


async def poll_once(provider: IFiatProvider) -> int:
    """Reconcile every pollable order once. Returns how many were checked."""
    async with AsyncSessionLocal() as db:
        orders = await OrderRepository.list_pollable(db)
        for order in orders:
            try:
                action = await reconcile_order(db, order, provider)
                if action != "none":
                    logger.info("reconciled order %s -> %s", order.id, action)
            except Exception:  # noqa: BLE001
                logger.exception("reconcile failed for order %s", order.id)
        return len(orders)


async def run_reconciler(stop: asyncio.Event) -> None:
    """Loop until stopped. Started/cancelled by the FastAPI lifespan."""
    provider = PaycrestProvider()
    logger.info("settlement reconciler started (every %ss)", POLL_INTERVAL_SECONDS)
    while not stop.is_set():
        try:
            await poll_once(provider)
        except Exception:  # noqa: BLE001
            logger.exception("reconciler poll cycle errored")
        try:
            await asyncio.wait_for(stop.wait(), timeout=POLL_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            pass
    logger.info("settlement reconciler stopped")
