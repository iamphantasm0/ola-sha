"""Single source of truth for applying a Paycrest order status to our order.

Both the webhook handler and the polling reconciler funnel through here, so a
status (whether pushed by webhook or pulled by poll) is handled identically. The
0G Storage + Chain writes are idempotent via the SETTLED guard, so it is always
safe to call this more than once for the same order.
"""

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal
from app.models.order import OrderStatus
from app.repositories.orders import OrderRepository
from app.services.memory import dataset_for_order, improve_memory, remember_fact
from app.services.notifications import push_status_update
from app.services.registry import log_to_registry
from app.services.storage import store_transaction_record

logger = logging.getLogger(__name__)

SETTLED = "settled"
VALIDATED = "validated"
PENDING = "pending"
FAILED_STATUSES = {"refunded", "expired"}

# Keep refs to fire-and-forget memory writes so they aren't garbage-collected mid-flight.
_memory_tasks: set = set()
_settle_count = 0  # drives periodic improve()/memify (every Nth settlement)
_IMPROVE_EVERY = 3


def _spawn(coro) -> None:
    """Fire-and-forget on the running loop, holding a ref so it isn't GC'd. Never blocks."""
    try:
        task = asyncio.create_task(coro)
        _memory_tasks.add(task)
        task.add_done_callback(_memory_tasks.discard)
    except RuntimeError:  # no running loop — skip silently
        pass


def _settlement_fact(order, direction: str) -> str:
    """A pattern-level fact for the memory graph — preferences ONLY, no account identifiers.

    Deliberately excludes bank name, account number (even last-4), account holder name, and
    wallet address: this string is sent to the 0G inference provider for entity extraction, and
    memory's value is the *preference*, not the account. Structured account details that actually
    get reused live in Postgres (saved accounts), never here. Amount/token/currency mirror what is
    already public in the on-chain 0G audit record, so they carry no extra exposure."""
    amt = f"{float(order.amount):g}" if order.amount else "?"
    fact = f"User completed a {direction} of {amt} {order.token} for {order.currency}."
    if direction == "offramp":
        fact += f" Prefers selling {order.token} to {order.currency}."
    elif direction == "onramp":
        if order.network:
            fact += f" Prefers receiving stablecoin on the {order.network} network."
        fact += f" Prefers buying {order.token} with {order.currency}."
    return fact


def _remember_settlement(order, direction: str) -> None:
    """Fire-and-forget: build the user's memory in the background; never blocks settlement.
    Every Nth settlement also runs improve()/memify to densify + prune the graph."""
    global _settle_count
    dataset = dataset_for_order(order)
    _spawn(remember_fact(dataset, _settlement_fact(order, direction)))
    _settle_count += 1
    if _settle_count % _IMPROVE_EVERY == 0:
        _spawn(improve_memory(dataset))


async def write_0g_records(db: AsyncSession, order, direction: str, data: dict) -> bool:
    """Write the audit record to 0G Storage + log to 0G Chain, then mark SETTLED.

    Idempotent: a no-op if the order is already SETTLED. Returns True on success.
    """
    if order.status == OrderStatus.SETTLED:
        return True

    record = {
        "order_id": str(order.id),
        "direction": direction,
        "token": order.token,
        "amount": float(order.amount) if order.amount else None,
        "currency": order.currency,
        "rate": float(order.rate) if order.rate else None,
        "output_amount": float(order.output_amount) if order.output_amount else None,
        "paycrest_order_id": order.paycrest_order_id,
        "tx_hash": data.get("txHash"),
        "status": data.get("status"),
        "settled_at": data.get("updatedAt"),
        "product": "Ola — a Sterling Concierge demo by Vela Labs",
        "version": "1.0.0",
    }
    try:
        storage_hash = await store_transaction_record(record)
        chain_tx = await log_to_registry(
            order_uuid=str(order.id),
            direction=direction,
            currency=order.currency,
            amount_cents=int(float(order.amount) * 100),
            storage_hash=storage_hash,
        )
        await OrderRepository.settle(db, str(order.id), storage_hash, chain_tx)
        await push_status_update(order.session_id, {
            "event": "settled", "status": "SETTLED",
            "storage_hash": storage_hash, "chain_tx": chain_tx,
        })
        _remember_settlement(order, direction)  # background, masked, never blocks
        return True
    except Exception:  # noqa: BLE001
        logger.exception("0G write failed for order %s", order.id)
        return False


async def write_0g_records_bg(order_id: str, direction: str, data: dict) -> None:
    """Webhook entry point: owns its own DB session (runs after the 200 response)."""
    async with AsyncSessionLocal() as db:
        order = await OrderRepository.get_by_id(db, order_id)
        if order:
            await write_0g_records(db, order, direction, data)


async def apply_status(db: AsyncSession, order, data: dict) -> str:
    """Apply a Paycrest status to the order. Used by both webhook and poller.

    Returns the action taken: "settled" | "processing" | "failed" | "none".
    0G writes (on settled) run inline here — callers that must respond fast
    (the webhook) should instead defer write_0g_records_bg and not call apply_status.
    """
    status = (data.get("status") or "").lower()
    direction = order.direction or data.get("direction", "")

    if status == SETTLED:
        if order.status != OrderStatus.SETTLED:
            await write_0g_records(db, order, direction, data)
        return "settled"

    if status == VALIDATED and direction == "offramp":
        if order.status != OrderStatus.OFFRAMP_PROCESSING:
            await OrderRepository.set_status(db, order, OrderStatus.OFFRAMP_PROCESSING)
        return "processing"

    if status == PENDING and direction == "onramp":
        if order.status != OrderStatus.ONRAMP_PROCESSING:
            await OrderRepository.set_status(db, order, OrderStatus.ONRAMP_PROCESSING)
        return "processing"

    if status in FAILED_STATUSES:
        if order.status != OrderStatus.FAILED:
            await OrderRepository.set_status(db, order, OrderStatus.FAILED)
        return "failed"

    return "none"
