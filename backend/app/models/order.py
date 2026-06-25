import enum
import uuid

from sqlalchemy import Column, Enum as SAEnum, ForeignKey, Numeric, String, Text
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
    OFFRAMP_AWAITING_DEPOSIT = "OFFRAMP_AWAITING_DEPOSIT"
    OFFRAMP_PROCESSING = "OFFRAMP_PROCESSING"

    # Onramp flow
    ONRAMP_QUOTING = "ONRAMP_QUOTING"
    ONRAMP_COLLECTING_WALLET = "ONRAMP_COLLECTING_WALLET"
    ONRAMP_AWAITING_PAYMENT = "ONRAMP_AWAITING_PAYMENT"
    ONRAMP_PROCESSING = "ONRAMP_PROCESSING"


# An order in any of these states is "in flight" for its session.
ACTIVE_STATUSES = {
    OrderStatus.OFFRAMP_QUOTING,
    OrderStatus.OFFRAMP_COLLECTING_BANK,
    OrderStatus.OFFRAMP_AWAITING_DEPOSIT,
    OrderStatus.OFFRAMP_PROCESSING,
    OrderStatus.ONRAMP_QUOTING,
    OrderStatus.ONRAMP_COLLECTING_WALLET,
    OrderStatus.ONRAMP_AWAITING_PAYMENT,
    OrderStatus.ONRAMP_PROCESSING,
}


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True
    )

    direction = Column(String(10), nullable=False)  # "onramp" | "offramp"
    token = Column(String(10), nullable=False)       # "USDC" | "USDT"
    amount = Column(Numeric(18, 6), nullable=False)   # crypto units (USD value)
    currency = Column(String(5), nullable=False)      # "NGN", "KES", ...
    rate = Column(Numeric(18, 6), nullable=True)
    output_amount = Column(Numeric(18, 2), nullable=True)

    # Paycrest
    paycrest_order_id = Column(String(100), nullable=True, unique=True, index=True)
    deposit_address = Column(String(120), nullable=True)   # offramp: where user sends crypto
    valid_until = Column(String(40), nullable=True)

    # 0G references (filled on settlement)
    storage_hash = Column(String(200), nullable=True)      # 0G Storage root hash
    registry_tx_hash = Column(String(80), nullable=True)   # 0G Chain tx hash

    status = Column(SAEnum(OrderStatus), nullable=False, default=OrderStatus.IDLE)

    # Offramp bank details
    bank_name = Column(String(100), nullable=True)
    institution_code = Column(String(40), nullable=True)
    account_number = Column(String(20), nullable=True)
    account_name = Column(String(200), nullable=True)

    # Onramp wallet details
    wallet_address = Column(String(42), nullable=True)
    network = Column(String(20), nullable=True)

    # Onramp: virtual bank account the user must pay into
    pay_bank_name = Column(String(120), nullable=True)
    pay_account_number = Column(String(40), nullable=True)
    pay_account_name = Column(String(200), nullable=True)
    pay_amount = Column(String(40), nullable=True)

    # Latest webhook event, surfaced to the UI via polling
    last_event = Column(String(60), nullable=True)
    last_event_message = Column(Text, nullable=True)

    session = relationship("Session", back_populates="orders")
