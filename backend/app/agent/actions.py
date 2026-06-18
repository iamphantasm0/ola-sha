"""Builds the button list the frontend renders for the current order state.

Confirmations and account selection happen via these buttons (hitting /action),
never through the chat model — so the money decisions are deterministic.
"""

from typing import Optional

from app.models.order import Order, OrderStatus
from app.models.user import SavedBankAccount, SavedWallet


def _bank_label(b: SavedBankAccount) -> str:
    tail = b.account_number[-4:] if b.account_number else ""
    return f"{b.bank_name} ••{tail} — {b.account_name}"


def _wallet_label(w: SavedWallet) -> str:
    a = w.address
    short = f"{a[:6]}…{a[-4:]}" if a else ""
    name = w.label or short
    return f"{name} ({w.network})"


def build_actions(
    order: Optional[Order],
    banks: Optional[list[SavedBankAccount]] = None,
    wallets: Optional[list[SavedWallet]] = None,
    *,
    bank_already_saved: bool = False,
) -> list[dict]:
    if not order:
        return []
    banks = banks or []
    wallets = wallets or []
    status = order.status

    if status == OrderStatus.OFFRAMP_QUOTING:
        acts = [
            {"type": "use_saved_bank", "label": _bank_label(b), "payload": {"saved_id": str(b.id)}}
            for b in banks if b.currency == order.currency
        ]
        acts.append({"type": "enter_bank", "label": "Use a different account"})
        acts.append({"type": "cancel", "label": "Cancel"})
        return acts

    if status == OrderStatus.OFFRAMP_CONFIRMING_BANK:
        acts = [{"type": "confirm_send", "label": "Confirm & get deposit address", "primary": True}]
        if not bank_already_saved:
            acts.append({"type": "save_bank", "label": "Save this account"})
        acts.append({"type": "cancel", "label": "Cancel"})
        return acts

    if status == OrderStatus.OFFRAMP_AWAITING_DEPOSIT:
        acts = []
        if not bank_already_saved:
            acts.append({"type": "save_bank", "label": "Save this account"})
        acts.append({"type": "check_status", "label": "I've sent it"})
        acts.append({"type": "cancel", "label": "Cancel"})
        return acts

    if status == OrderStatus.ONRAMP_QUOTING:
        acts = [
            {"type": "use_saved_wallet", "label": _wallet_label(w), "payload": {"saved_id": str(w.id)}}
            for w in wallets
        ]
        acts.append({"type": "enter_wallet", "label": "Use a different wallet"})
        acts.append({"type": "cancel", "label": "Cancel"})
        return acts

    if status == OrderStatus.ONRAMP_AWAITING_PAYMENT:
        return [
            {"type": "check_status", "label": "I've paid"},
            {"type": "cancel", "label": "Cancel"},
        ]

    return []
