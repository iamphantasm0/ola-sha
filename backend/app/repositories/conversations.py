import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationMessage


class ConversationRepository:
    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        tool_name: Optional[str] = None,
    ) -> ConversationMessage:
        msg = ConversationMessage(
            session_id=uuid.UUID(str(session_id)),
            role=role,
            content=content or "",
            tool_name=tool_name,
        )
        db.add(msg)
        await db.commit()
        return msg

    @staticmethod
    async def get_history(db: AsyncSession, session_id: str, limit: int = 20) -> list[dict]:
        """Return the last `limit` messages in chronological order as OpenAI-style dicts.

        Only user/assistant text turns are replayed — tool-call plumbing is rebuilt
        fresh each request, so we never replay orphaned tool messages.
        """
        result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == uuid.UUID(str(session_id)))
            .where(ConversationMessage.role.in_(["user", "assistant"]))
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        rows = list(result.scalars().all())[::-1]
        return [{"role": r.role, "content": r.content} for r in rows]
