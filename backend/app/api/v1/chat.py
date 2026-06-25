import json
import logging

from fastapi import APIRouter, Depends

from app.agent.client import og_client
from app.agent.dispatcher import dispatch_tool_call
from app.agent.prompts import build_system_prompt
from app.agent.tools import ALL_TOOLS, TOOLS_BY_STATE
from app.core.config import settings
from app.core.dependencies import get_db
from app.providers.paycrest import PaycrestProvider
from app.repositories.conversations import ConversationRepository
from app.repositories.orders import OrderRepository
from app.repositories.sessions import SessionRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.order import serialize_order

logger = logging.getLogger(__name__)
router = APIRouter()
provider = PaycrestProvider()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db=Depends(get_db)):
    # 1. Session + active order + state
    await SessionRepository.get_or_create(db, req.session_id)
    order = await OrderRepository.get_active_by_session(db, req.session_id)
    current_state = order.status.value if order else "IDLE"

    # 2. History + persist the new user turn
    history = await ConversationRepository.get_history(db, req.session_id, limit=20)
    await ConversationRepository.add_message(
        db, req.session_id, role="user", content=req.message
    )

    # 3. Inject ONLY the tools valid for the current state
    allowed_tool_names = TOOLS_BY_STATE.get(current_state, [])
    tools = [ALL_TOOLS[n] for n in allowed_tool_names] or None

    messages = [
        {"role": "system", "content": build_system_prompt(current_state, order)},
        *history,
        {"role": "user", "content": req.message},
    ]

    # 4. First model call
    response = await og_client.chat.completions.create(
        model=settings.OG_COMPUTE_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto" if tools else None,
        max_tokens=500,
        temperature=0.2,
    )
    choice = response.choices[0]
    tool_called = None

    if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
        tool_call = choice.message.tool_calls[0]
        tool_name = tool_call.function.name
        try:
            tool_args = json.loads(tool_call.function.arguments or "{}")
        except json.JSONDecodeError:
            tool_args = {}
        tool_called = tool_name

        # 5. Dispatch through the firewall (state gate re-checked inside)
        tool_result = await dispatch_tool_call(
            tool_name=tool_name,
            tool_args=tool_args,
            current_state=current_state,
            order=order,
            session_id=req.session_id,
            provider=provider,
            db_session=db,
        )

        # 6. Second model call with the tool result. We rebuild the assistant
        #    message with exactly the one tool_call we handled so the message
        #    array stays valid even if the model emitted several.
        messages.append(
            {
                "role": "assistant",
                "content": choice.message.content or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": tool_call.function.arguments or "{}",
                        },
                    }
                ],
            }
        )
        messages.append(
            {"role": "tool", "tool_call_id": tool_call.id, "content": tool_result}
        )

        followup = await og_client.chat.completions.create(
            model=settings.OG_COMPUTE_MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0.2,
        )
        reply = followup.choices[0].message.content or ""
    else:
        reply = choice.message.content or ""

    # 7. Persist assistant reply
    await ConversationRepository.add_message(
        db, req.session_id, role="assistant", content=reply
    )

    # 8. Reload order for the response payload
    order = await OrderRepository.get_active_by_session(
        db, req.session_id
    ) or await OrderRepository.get_latest_by_session(db, req.session_id)

    return ChatResponse(
        reply=reply, order_state=serialize_order(order), tool_called=tool_called
    )
