"""Public proof endpoint — anyone can verify a settlement's 0G records, no auth.

Exposes only non-PII fields (amounts, currency, hashes) — never bank/wallet details.
Everything returned is already public on 0G Storage + Chain.
"""

import re
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models.order import Order, OrderStatus
from app.repositories.orders import OrderRepository
from app.services.storage import fetch_transaction_record

router = APIRouter()

STORAGE_SCAN = "https://storagescan-galileo.0g.ai/tx"
CHAIN_SCAN = "https://chainscan-galileo.0g.ai/tx"

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_HEX_RE = re.compile(r"^0x[0-9a-f]+$", re.IGNORECASE)


def _public(o: Order) -> dict:
    return {
        "order_id": str(o.id),
        "direction": o.direction,
        "amount": float(o.amount) if o.amount else None,
        "token": o.token,
        "currency": o.currency,
        "output_amount": float(o.output_amount) if o.output_amount else None,
        "settled_at": o.updated_at.isoformat() if o.updated_at else None,
        "storage_hash": o.storage_hash,
        "registry_tx_hash": o.registry_tx_hash,
        "storage_url": f"{STORAGE_SCAN}/{o.storage_hash}" if o.storage_hash else None,
        "chain_url": f"{CHAIN_SCAN}/{o.registry_tx_hash}" if o.registry_tx_hash else None,
    }


async def _live_proof(o: Order) -> dict:
    """Summary + live 0G Storage retrieval + live Chain receipt check."""
    data = _public(o)

    record = None
    if o.storage_hash:
        try:
            record = await fetch_transaction_record(o.storage_hash)
        except Exception:  # noqa: BLE001
            record = None
    data["storage_record"] = record

    chain = {"verified": False}
    if o.registry_tx_hash:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(
                    settings.OG_CHAIN_RPC,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "eth_getTransactionReceipt",
                        "params": [o.registry_tx_hash],
                    },
                )
                rec = r.json().get("result")
                if rec:
                    chain = {
                        "verified": rec.get("status") == "0x1",
                        "block": int(rec["blockNumber"], 16),
                        "contract": rec.get("to"),
                        "events": len(rec.get("logs", [])),
                    }
        except Exception:  # noqa: BLE001
            pass
    data["chain"] = chain
    return data


def _normalize_lookup_id(raw: str) -> str:
    """Trim and fix common paste variants (missing 0x prefix, 8x typo for 0x)."""
    q = raw.strip()
    if _HEX_RE.match(q):
        return q.lower()
    # 64-char hex without prefix (storage roots are 32 bytes)
    if re.fullmatch(r"[0-9a-fA-F]{64}", q):
        return f"0x{q.lower()}"
    # Common mistype: 8x instead of 0x
    if re.fullmatch(r"8x[0-9a-fA-F]{64}", q, re.IGNORECASE):
        return f"0x{q[2:].lower()}"
    return q


async def _resolve_settled_order(db: AsyncSession, raw: str) -> tuple[Optional[Order], Optional[str]]:
    """Map a pasted id to a settled order. Returns (order, matched_by)."""
    q = _normalize_lookup_id(raw)
    if not q:
        return None, None

    if _UUID_RE.match(q):
        o = await OrderRepository.get_settled_by_id(db, q)
        return (o, "order_id") if o else (None, None)

    if _HEX_RE.match(q):
        needle = q.lower()
        o = await OrderRepository.get_settled_by_registry_tx(db, needle)
        if o:
            return o, "registry_tx_hash"
        o = await OrderRepository.get_settled_by_storage_hash(db, needle)
        if o:
            return o, "storage_hash"
        # Case mismatch in DB — try original casing too.
        o = await OrderRepository.get_settled_by_registry_tx(db, q)
        if o:
            return o, "registry_tx_hash"
        o = await OrderRepository.get_settled_by_storage_hash(db, q)
        if o:
            return o, "storage_hash"
        return None, None

    o = await OrderRepository.get_settled_by_paycrest_id(db, q)
    if o:
        return o, "paycrest_order_id"
    return None, None


@router.get("/verify/recent")
async def recent(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=8, ge=1, le=50),
    cursor: Optional[str] = Query(default=None),
):
    """Recent settled orders. Optional cursor pagination via settled_at ISO timestamp."""
    q = (
        select(Order)
        .where(Order.status == OrderStatus.SETTLED)
        .where(Order.storage_hash.isnot(None))
        .order_by(Order.updated_at.desc())
    )
    if cursor:
        try:
            ts = datetime.fromisoformat(cursor)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")
        q = q.where(Order.updated_at < ts)

    q = q.limit(limit + 1)
    rows = list((await db.execute(q)).scalars().all())

    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = page[-1].updated_at.isoformat() if has_more and page else None

    return {
        "settlements": [_public(o) for o in page],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@router.get("/verify/lookup")
async def verify_lookup(q: str = Query(..., min_length=1), db: AsyncSession = Depends(get_db)):
    """Resolve any public id (order UUID, storage hash, chain tx, Paycrest ref) and verify live."""
    order, matched_by = await _resolve_settled_order(db, q)
    if not order:
        raise HTTPException(status_code=404, detail="No settled transaction found for that id")

    data = await _live_proof(order)
    data["matched_by"] = matched_by
    return data


@router.get("/verify/order/{order_id}")
async def verify_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """Full proof by order UUID — kept for backward compatibility."""
    try:
        uuid.UUID(order_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid order id")

    order = await OrderRepository.get_settled_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="No settled order with that id")

    data = await _live_proof(order)
    data["matched_by"] = "order_id"
    return data