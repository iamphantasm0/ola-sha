import uuid

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Session(Base, TimestampMixin):
    """One browser session = one chat thread. No login for the MVP."""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    orders = relationship("Order", back_populates="session")
    messages = relationship("ConversationMessage", back_populates="session")
