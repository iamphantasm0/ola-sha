from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Session(Base, TimestampMixin):
    """One browser session = one chat thread. Anonymous (no login) for MVP."""

    __tablename__ = "sessions"

    orders = relationship("Order", back_populates="session")
