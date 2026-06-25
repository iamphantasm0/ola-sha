import uuid

from app.models.session import Session


class SessionRepository:
    @staticmethod
    async def get_or_create(db, session_id: str) -> Session:
        """The frontend mints a UUID in localStorage; we adopt it as the PK."""
        sid = uuid.UUID(str(session_id))
        existing = await db.get(Session, sid)
        if existing:
            return existing
        sess = Session(id=sid)
        db.add(sess)
        await db.flush()
        return sess
