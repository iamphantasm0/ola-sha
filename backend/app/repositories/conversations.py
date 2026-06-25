import uuid

from sqlalchemy import select

from app.models.conversation import ConversationMessage


class ConversationRepository:
    @staticmethod
    async def add_message(db, session_id, role, content, tool_name=None):
        msg = ConversationMessage(
            session_id=uuid.UUID(str(session_id)),
            role=role,
            content=content or "",
            tool_name=tool_name,
        )
        db.add(msg)
        await db.flush()
        return msg

    @staticmethod
    async def get_history(db, session_id, limit: int = 20):
        """
        Return the last N user/assistant turns as OpenAI-style dicts.

        Tool messages are intentionally excluded: replaying bare tool results
        across turns would require re-pairing every tool_call_id, which adds
        fragility for no benefit. The system prompt already carries the order
        state the model needs.
        """
        q = (
            select(ConversationMessage)
            .where(ConversationMessage.session_id == uuid.UUID(str(session_id)))
            .where(ConversationMessage.role.in_(["user", "assistant"]))
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        rows = (await db.execute(q)).scalars().all()
        rows = list(reversed(rows))
        return [{"role": m.role, "content": m.content} for m in rows]
