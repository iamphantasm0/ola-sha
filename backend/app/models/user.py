from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)

    bank_accounts = relationship("SavedBankAccount", back_populates="user", cascade="all, delete-orphan")
    wallets = relationship("SavedWallet", back_populates="user", cascade="all, delete-orphan")


class SavedBankAccount(Base, TimestampMixin):
    """A bank account the user has verified and chosen to remember (for offramp)."""

    __tablename__ = "saved_bank_accounts"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    currency = Column(String(5), nullable=False)            # NGN, KES, ...
    bank_name = Column(String(100), nullable=False)         # as the user typed it
    institution_code = Column(String(40), nullable=False)   # Paycrest code
    account_number = Column(String(20), nullable=False)
    account_name = Column(String(200), nullable=False)      # verified canonical name
    label = Column(String(60), nullable=True)               # optional nickname

    user = relationship("User", back_populates="bank_accounts")


class SavedWallet(Base, TimestampMixin):
    """A wallet address the user has chosen to remember (for onramp)."""

    __tablename__ = "saved_wallets"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    address = Column(String(42), nullable=False)
    network = Column(String(20), nullable=False)
    label = Column(String(60), nullable=True)

    user = relationship("User", back_populates="wallets")
