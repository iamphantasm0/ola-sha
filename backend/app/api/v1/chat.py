import json
import logging
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.client import og_client
from app.agent.dispatcher import dispatch_tool_call
from app.agent.presenter import render_tool_reply
from app.agent.prompts import build_system_prompt
from app.agent.tools import ALL_TOOLS, TOOLS_BY_STATE
from app.api.v1.common import assemble_response
from app.core.config import settings
from app.core.db import get_db
from app.core.dependencies import get_optional_user
from app.models.user import User
from app.providers.paycrest import PaycrestProvider
from app.repositories.conversations import ConversationRepository
from app.repositories.orders import OrderRepository
from app.repositories.sessions import SessionRepository

logger = logging.getLogger(__name__)
router = APIRouter()
provider = PaycrestProvider()

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _strip_reasoning(text: str) -> str:
    """Remove <think>…</think> blocks (minimax-m3 reasons out loud by default)."""
    if not text:
        return text
    cleaned = _THINK_RE.sub("", text)
    # Drop a dangling unclosed <think> … (truncated reasoning) too.
    cleaned = re.sub(r"<think>.*$", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    return cleaned.strip()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
async def chat(
    req: ChatRequest,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        uuid.UUID(str(req.session_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="session_id must be a valid UUID")

    await SessionRepository.get_or_create(db, req.session_id)

    order = await OrderRepository.get_active_by_session(db, req.session_id)
    current_state = order.status.value if order else "IDLE"

    history = await ConversationRepository.get_history(db, req.session_id, limit=20)
    await ConversationRepository.add_message(db, req.session_id, "user", req.message)

    allowed = TOOLS_BY_STATE.get(current_state, [])
    tools = [ALL_TOOLS[name] for name in allowed] or None

    messages = [
        {"role": "system", "content": build_system_prompt(current_state, order)},
        *history,
        {"role": "user", "content": req.message},
    ]

    response = await og_client.chat.completions.create(
        model=settings.OG_COMPUTE_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto" if tools else None,
        max_tokens=600,
        temperature=0.2,
    )
    choice = response.choices[0]
    tool_called = None

    if choice.message.tool_calls:
        tc = choice.message.tool_calls[0]  # state gate enforces one logical step at a time
        tool_called = tc.function.name
        try:
            tool_args = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            tool_args = {}

        tool_result = await dispatch_tool_call(
            tool_name=tc.function.name,
            tool_args=tool_args,
            current_state=current_state,
            order=order,
            session_id=req.session_id,
            provider=provider,
            db=db,
        )

        # Money-critical data (addresses, accounts, amounts) is rendered deterministically
        # from the tool result — the model must NOT free-form it (it hallucinates otherwise).
        reply = render_tool_reply(tc.function.name, tool_result)
        if reply is None:
            messages.append(choice.message.model_dump())
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": tool_result})
            followup = await og_client.chat.completions.create(
                model=settings.OG_COMPUTE_MODEL,
                messages=messages,
                max_tokens=400,
                temperature=0.2,
            )
            reply = followup.choices[0].message.content or ""
    else:
        reply = choice.message.content or ""

    reply = _strip_reasoning(reply)
    await ConversationRepository.add_message(db, req.session_id, "assistant", reply)

    order = await OrderRepository.get_latest_by_session(db, req.session_id)
    if user and order and not order.user_id:
        await OrderRepository.update(db, order, user_id=user.id)
    return await assemble_response(db, order, user, reply, tool_called)
