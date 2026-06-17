from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories.orders import OrderRepository

router = APIRouter()


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    x_session_id: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Frontend polls this for live status (the source of truth for the sidebar).

    Ownership-scoped: the caller must present the session id that owns the order.
    A mismatch returns 404 (not 403) so order existence can't be enumerated.
    """
    order = await OrderRepository.get_by_id(db, order_id)
    if not order or not x_session_id or str(order.session_id) != x_session_id:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_id": str(order.id),
        "status": order.status.value,
        "direction": order.direction,
        "amount": float(order.amount) if order.amount else None,
        "token": order.token,
        "currency": order.currency,
        "output_amount": float(order.output_amount) if order.output_amount else None,
        "deposit_address": order.deposit_address,
        "storage_hash": order.storage_hash,
        "registry_tx_hash": order.registry_tx_hash,
        "paycrest_order_id": order.paycrest_order_id,
    }
