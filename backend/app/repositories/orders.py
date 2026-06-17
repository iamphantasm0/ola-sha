import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus, TERMINAL_STATES


class OrderRepository:
    @staticmethod
    async def get_active_by_session(db: AsyncSession, session_id: str) -> Optional[Order]:
        """Most recent non-terminal order for the session (the one in progress)."""
        result = await db.execute(
            select(Order)
            .where(Order.session_id == uuid.UUID(str(session_id)))
            .where(Order.status.notin_(list(TERMINAL_STATES)))
            .order_by(Order.created_at.desc())
        )
        return result.scalars().first()

    @staticmethod
    async def get_latest_by_session(db: AsyncSession, session_id: str) -> Optional[Order]:
        result = await db.execute(
            select(Order)
            .where(Order.session_id == uuid.UUID(str(session_id)))
            .order_by(Order.created_at.desc())
        )
        return result.scalars().first()

    @staticmethod
    async def get_by_id(db: AsyncSession, order_id: str) -> Optional[Order]:
        return await db.get(Order, uuid.UUID(str(order_id)))

    @staticmethod
    async def get_by_paycrest_id(db: AsyncSession, paycrest_id: str) -> Optional[Order]:
        result = await db.execute(
            select(Order).where(Order.paycrest_order_id == paycrest_id)
        )
        return result.scalars().first()

    @staticmethod
    async def list_pollable(db: AsyncSession) -> list[Order]:
        """Non-terminal orders that have a Paycrest id — i.e. awaiting/processing.

        These are the only orders whose Paycrest status can still change, so the
        poller checks just these (quote/collecting states have no provider id yet).
        """
        result = await db.execute(
            select(Order)
            .where(Order.paycrest_order_id.isnot(None))
            .where(Order.status.notin_(list(TERMINAL_STATES)))
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_quote(
        db: AsyncSession,
        session_id: str,
        direction: str,
        token: str,
        amount: float,
        currency: str,
        rate: float,
        output_amount: float,
        status: OrderStatus,
    ) -> Order:
        """Create a pending order from a quote AND set the QUOTING state."""
        order = Order(
            session_id=uuid.UUID(str(session_id)),
            direction=direction,
            token=token,
            amount=amount,
            currency=currency,
            rate=rate,
            output_amount=output_amount,
            status=status,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def set_status(db: AsyncSession, order: Order, status: OrderStatus) -> Order:
        order.status = status
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def update(db: AsyncSession, order: Order, **fields) -> Order:
        for k, v in fields.items():
            setattr(order, k, v)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def settle(
        db: AsyncSession, order_id: str, storage_hash: str, registry_tx_hash: str
    ) -> Optional[Order]:
        order = await db.get(Order, uuid.UUID(str(order_id)))
        if not order:
            return None
        order.storage_hash = storage_hash
        order.registry_tx_hash = registry_tx_hash
        order.status = OrderStatus.SETTLED
        await db.commit()
        await db.refresh(order)
        return order
