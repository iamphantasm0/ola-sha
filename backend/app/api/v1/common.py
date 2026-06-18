from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.actions import build_actions
from app.models.order import Order
from app.models.user import User
from app.repositories.accounts import AccountRepository


def order_state_json(order: Optional[Order]) -> Optional[dict]:
    if not order:
        return None
    return {
        "order_id": str(order.id),
        "status": order.status.value,
        "direction": order.direction,
        "amount": float(order.amount) if order.amount else None,
        "token": order.token,
        "currency": order.currency,
        "output_amount": float(order.output_amount) if order.output_amount else None,
        "account_name": order.account_name,
        "bank_name": order.bank_name,
        "account_number": order.account_number,
        "deposit_address": order.deposit_address,
        "storage_hash": order.storage_hash,
        "registry_tx_hash": order.registry_tx_hash,
        "paycrest_order_id": order.paycrest_order_id,
    }


async def assemble_response(
    db: AsyncSession,
    order: Optional[Order],
    user: Optional[User],
    reply: str,
    tool_called: Optional[str] = None,
) -> dict:
    """Build the unified chat/action response: reply + order state + state-appropriate buttons."""
    banks: list = []
    wallets: list = []
    bank_already_saved = False
    if user and order:
        banks = await AccountRepository.list_banks(db, user.id)
        wallets = await AccountRepository.list_wallets(db, user.id)
        if order.institution_code and order.account_number:
            existing = await AccountRepository.find_bank(
                db, user.id, order.currency, order.institution_code, order.account_number
            )
            bank_already_saved = existing is not None
    actions = build_actions(order, banks, wallets, bank_already_saved=bank_already_saved)
    return {
        "reply": reply,
        "order_state": order_state_json(order),
        "actions": actions,
        "tool_called": tool_called,
        "authenticated": user is not None,
    }
