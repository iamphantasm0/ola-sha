from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_db
from app.repositories.orders import OrderRepository
from app.schemas.order import serialize_order

router = APIRouter()


@router.get("/orders/{order_id}")
async def get_order(order_id: str, db=Depends(get_db)):
    order = await OrderRepository.get(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return serialize_order(order)


@router.get("/sessions/{session_id}/order")
async def get_session_order(session_id: str, db=Depends(get_db)):
    """Latest order for a session — used by the frontend to poll for
    webhook-driven status changes (e.g. SETTLED)."""
    order = await OrderRepository.get_active_by_session(
        db, session_id
    ) or await OrderRepository.get_latest_by_session(db, session_id)
    return serialize_order(order)
