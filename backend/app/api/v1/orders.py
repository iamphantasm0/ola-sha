from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.orders import OrderRepository

router = APIRouter()


def _history_order_json(order) -> dict:
    """Ramp summary for the signed-in user's history — no raw account numbers."""
    return {
        "order_id": str(order.id),
        "status": order.status.value,
        "direction": order.direction,
        "amount": float(order.amount) if order.amount else None,
        "token": order.token,
        "currency": order.currency,
        "output_amount": float(order.output_amount) if order.output_amount else None,
        "storage_hash": order.storage_hash,
        "registry_tx_hash": order.registry_tx_hash,
        "paycrest_order_id": order.paycrest_order_id,
        "deposit_address": order.deposit_address,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }


@router.get("/orders/history")
async def order_history(
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the authenticated user's past ramps (paginated, newest first)."""
    parsed_cursor: datetime | None = None
    if cursor:
        try:
            parsed_cursor = datetime.fromisoformat(cursor.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor")

    orders, next_cursor, has_more = await OrderRepository.list_by_user(
        db, user.id, limit=limit, cursor=parsed_cursor,
    )
    return {
        "orders": [_history_order_json(o) for o in orders],
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


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
