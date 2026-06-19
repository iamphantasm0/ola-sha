"""Public proof endpoint — anyone can verify a settlement's 0G records, no auth.

Exposes only non-PII fields (amounts, currency, hashes) — never bank/wallet details.
Everything returned is already public on 0G Storage + Chain.
"""

import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.models.order import Order, OrderStatus
from app.services.storage import fetch_transaction_record

router = APIRouter()

STORAGE_SCAN = "https://storagescan-galileo.0g.ai/tx"
CHAIN_SCAN = "https://chainscan-galileo.0g.ai/tx"


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


@router.get("/verify/recent")
async def recent(db: AsyncSession = Depends(get_db)):
    """Recent settled orders, so the verify page always has live proofs to click."""
    q = (
        select(Order)
        .where(Order.status == OrderStatus.SETTLED)
        .where(Order.storage_hash.isnot(None))
        .order_by(Order.updated_at.desc())
        .limit(8)
    )
    rows = list((await db.execute(q)).scalars().all())
    return {"settlements": [_public(o) for o in rows]}


@router.get("/verify/order/{order_id}")
async def verify_order(order_id: str, db: AsyncSession = Depends(get_db)):
    """Full proof: live retrieval of the 0G Storage record + live 0G Chain receipt check."""
    try:
        oid = uuid.UUID(order_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid order id")
    o = await db.get(Order, oid)
    if not o or o.status != OrderStatus.SETTLED:
        raise HTTPException(status_code=404, detail="No settled order with that id")

    data = _public(o)

    # 1) prove the record is retrievable from 0G Storage right now
    record = None
    if o.storage_hash:
        try:
            record = await fetch_transaction_record(o.storage_hash)
        except Exception:  # noqa: BLE001
            record = None
    data["storage_record"] = record

    # 2) prove the settlement tx is real on 0G Chain right now
    chain = {"verified": False}
    if o.registry_tx_hash:
        try:
            async with httpx.AsyncClient(timeout=15.0) as c:
                r = await c.post(
                    settings.OG_CHAIN_RPC,
                    json={"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt",
                          "params": [o.registry_tx_hash]},
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
