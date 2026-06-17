import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session


class SessionRepository:
    @staticmethod
    async def get_or_create(db: AsyncSession, session_id: str) -> Session:
        sid = uuid.UUID(str(session_id))
        existing = await db.get(Session, sid)
        if existing:
            return existing
        session = Session(id=sid)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
