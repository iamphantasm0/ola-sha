"""Deterministic button actions — confirmations and account selection without the AI."""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.presenter import render_tool_reply
from app.api.v1.common import assemble_response, ensure_order_access
from app.core.db import get_db
from app.core.dependencies import get_optional_user
from app.models.user import User
from app.providers.paycrest import PaycrestProvider
from app.repositories.accounts import AccountRepository
from app.repositories.orders import OrderRepository
from app.services import orders_flow
from app.services.settlement import apply_status

router = APIRouter()
provider = PaycrestProvider()


class ActionRequest(BaseModel):
    session_id: str
    action: str
    payload: dict = {}


def _render(tool_name: str, result: dict) -> str:
    return render_tool_reply(tool_name, json.dumps(result)) or ""


@router.post("/action")
async def action(
    req: ActionRequest,
    user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        uuid.UUID(req.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="session_id must be a valid UUID")

    order = await OrderRepository.get_active_by_session(db, req.session_id)
    if not order:
        raise HTTPException(status_code=409, detail="No active order for this session")
    # 403 if this order belongs to another account; binds anonymous orders to the caller.
    await ensure_order_access(db, order, user)

    a, p = req.action, req.payload or {}

    if a == "cancel":
        await orders_flow.cancel(db, order)
        reply = "Your order has been cancelled. Want to start a new buy or sell?"

    elif a == "use_saved_bank":
        if not user:
            raise HTTPException(status_code=401, detail="Login required")
        acct = await AccountRepository.get_bank(db, p.get("saved_id"), user.id)
        if not acct:
            raise HTTPException(status_code=404, detail="Saved account not found")
        res = await orders_flow.stage_bank(
            db, order, provider, acct.bank_name, acct.account_number,
            institution_code=acct.institution_code, account_name=acct.account_name,
        )
        reply = _render("submit_bank_details", res)

    elif a == "submit_bank":
        res = await orders_flow.stage_bank(db, order, provider, p.get("bank_name", ""), p.get("account_number", ""))
        reply = _render("submit_bank_details", res)

    elif a == "confirm_send":
        if order.direction == "offramp":
            res = await orders_flow.create_offramp(db, order, provider, req.session_id)
            reply = _render("confirm_bank_details", res) if "error" not in res else res["error"]
        else:
            raise HTTPException(status_code=409, detail="Nothing to confirm")

    elif a == "save_bank":
        if not user:
            raise HTTPException(status_code=401, detail="Login required")
        if order.institution_code:
            await AccountRepository.add_bank(
                db, user.id, order.currency, order.bank_name, order.institution_code,
                order.account_number, order.account_name,
            )
        reply = "Saved. ✅ I'll offer this account next time."

    elif a == "use_saved_wallet":
        if not user:
            raise HTTPException(status_code=401, detail="Login required")
        w = await AccountRepository.get_wallet(db, p.get("saved_id"), user.id)
        if not w:
            raise HTTPException(status_code=404, detail="Saved wallet not found")
        res = await orders_flow.create_onramp(db, order, provider, req.session_id, w.address, w.network)
        reply = _render("submit_wallet_address", res)

    elif a == "submit_wallet":
        res = await orders_flow.create_onramp(db, order, provider, req.session_id, p.get("address", ""), p.get("network", ""))
        reply = _render("submit_wallet_address", res)

    elif a == "check_status":
        if order.paycrest_order_id:
            data = await provider.get_order_status(order.paycrest_order_id)
            await apply_status(db, order, data)
            order = await OrderRepository.get_by_id(db, str(order.id))
            reply = _render("check_deposit_status", {
                "paycrest_status": data.get("status", "pending"),
                "order_status": order.status.value,
            })
        else:
            reply = "I don't see a submitted order yet."

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {a}")

    order = await OrderRepository.get_latest_by_session(db, req.session_id)
    return await assemble_response(db, order, user, reply)
