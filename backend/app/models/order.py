import enum

from sqlalchemy import Column, ForeignKey, Numeric, String, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class OrderStatus(enum.Enum):
    # Shared
    IDLE = "IDLE"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    SETTLED = "SETTLED"

    # Offramp flow
    OFFRAMP_QUOTING = "OFFRAMP_QUOTING"
    OFFRAMP_COLLECTING_BANK = "OFFRAMP_COLLECTING_BANK"
    OFFRAMP_CONFIRMING_BANK = "OFFRAMP_CONFIRMING_BANK"
    OFFRAMP_AWAITING_DEPOSIT = "OFFRAMP_AWAITING_DEPOSIT"
    OFFRAMP_PROCESSING = "OFFRAMP_PROCESSING"

    # Onramp flow
    ONRAMP_QUOTING = "ONRAMP_QUOTING"
    ONRAMP_COLLECTING_WALLET = "ONRAMP_COLLECTING_WALLET"
    ONRAMP_AWAITING_PAYMENT = "ONRAMP_AWAITING_PAYMENT"
    ONRAMP_PROCESSING = "ONRAMP_PROCESSING"


# Terminal states — an order in one of these is no longer "active".
TERMINAL_STATES = {OrderStatus.SETTLED, OrderStatus.FAILED, OrderStatus.CANCELLED}


class OrderStatusType(TypeDecorator):
    """Stores OrderStatus as a plain VARCHAR (the enum value), not a native PG enum.

    Avoids the "ALTER TYPE ... ADD VALUE" migration pain: new states just work, since
    nothing at the DB level constrains the column to a fixed value set.
    """

    impl = String(40)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.value if isinstance(value, OrderStatus) else str(value)

    def process_result_value(self, value, dialect):
        return OrderStatus(value) if value is not None else None


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    direction = Column(String(10), nullable=True)  # "onramp" | "offramp"
    token = Column(String(10), nullable=True)  # "USDC" | "USDT"
    amount = Column(Numeric(18, 6), nullable=True)
    currency = Column(String(5), nullable=True)  # "NGN", "KES", etc.
    rate = Column(Numeric(18, 6), nullable=True)
    output_amount = Column(Numeric(18, 2), nullable=True)

    # Paycrest
    paycrest_order_id = Column(String(100), nullable=True, unique=True, index=True)

    # 0G references
    storage_hash = Column(String(200), nullable=True)
    registry_tx_hash = Column(String(66), nullable=True)

    # State
    status = Column(OrderStatusType, nullable=False, default=OrderStatus.IDLE)

    # Offramp bank details
    bank_name = Column(String(100), nullable=True)
    institution_code = Column(String(40), nullable=True)
    account_number = Column(String(20), nullable=True)
    account_name = Column(String(200), nullable=True)

    # Onramp wallet details
    wallet_address = Column(String(42), nullable=True)
    network = Column(String(20), nullable=True)

    # Payment instructions to redisplay (deposit address / bank account)
    deposit_address = Column(String(64), nullable=True)

    session = relationship("Session", back_populates="orders")
