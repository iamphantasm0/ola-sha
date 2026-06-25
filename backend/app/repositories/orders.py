import uuid

from sqlalchemy import select

from app.models.order import ACTIVE_STATUSES, Order, OrderStatus


class OrderRepository:
    @staticmethod
    async def get(db, order_id):
        return await db.get(Order, uuid.UUID(str(order_id)))

    @staticmethod
    async def get_active_by_session(db, session_id):
        sid = uuid.UUID(str(session_id))
        q = (
            select(Order)
            .where(Order.session_id == sid)
            .where(Order.status.in_(list(ACTIVE_STATUSES)))
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        return (await db.execute(q)).scalars().first()

    @staticmethod
    async def get_latest_by_session(db, session_id):
        sid = uuid.UUID(str(session_id))
        q = (
            select(Order)
            .where(Order.session_id == sid)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        return (await db.execute(q)).scalars().first()

    @staticmethod
    async def get_by_paycrest_id(db, paycrest_id):
        q = select(Order).where(Order.paycrest_order_id == paycrest_id).limit(1)
        return (await db.execute(q)).scalars().first()

    @staticmethod
    async def cancel_active_for_session(db, session_id):
        """A fresh quote supersedes any in-flight quote for the same session."""
        sid = uuid.UUID(str(session_id))
        q = (
            select(Order)
            .where(Order.session_id == sid)
            .where(Order.status.in_(list(ACTIVE_STATUSES)))
        )
        for order in (await db.execute(q)).scalars().all():
            order.status = OrderStatus.CANCELLED
        await db.flush()

    @staticmethod
    async def create_quote(
        db, session_id, direction, token, amount, currency, rate, output_amount, status
    ):
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
        await db.flush()
        return order

    @staticmethod
    async def update_status(db, order_id, status):
        order = await db.get(Order, uuid.UUID(str(order_id)))
        if order:
            order.status = status
            await db.flush()
        return order

    @staticmethod
    async def settle(db, order_id, storage_hash, registry_tx_hash):
        order = await db.get(Order, uuid.UUID(str(order_id)))
        if order:
            order.status = OrderStatus.SETTLED
            order.storage_hash = storage_hash
            order.registry_tx_hash = registry_tx_hash
            await db.flush()
        return order
