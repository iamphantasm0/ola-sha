"""The firewall: executes tool calls, enforces the state gate, transitions DB state.

Rules:
  - ALWAYS re-check the state gate before executing (defense in depth).
  - Paycrest order creation happens ONLY in submit_bank_details / submit_wallet_address.
  - 0G Storage + Chain writes happen ONLY in the webhook handler, never here.
"""

import json
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import TOOLS_BY_STATE
from app.models.order import Order, OrderStatus
from app.providers.base import IFiatProvider
from app.repositories.accounts import AccountRepository
from app.repositories.orders import OrderRepository
from app.services import orders_flow
from app.services.settlement import apply_status

logger = logging.getLogger(__name__)

SAFE_FALLBACK = "I can't do that at this stage. Let's continue with your current step."


async def dispatch_tool_call(
    tool_name: str,
    tool_args: dict,
    current_state: str,
    order: Optional[Order],
    session_id: str,
    provider: IFiatProvider,
    db: AsyncSession,
    user=None,
) -> str:
    allowed = TOOLS_BY_STATE.get(current_state, [])
    if tool_name not in allowed:
        logger.warning("BLOCKED %s in state %s (session=%s)", tool_name, current_state, session_id)
        return SAFE_FALLBACK

    handlers = {
        "get_offramp_quote": _get_offramp_quote,
        "get_onramp_quote": _get_onramp_quote,
        "confirm_offramp": _confirm_offramp,
        "confirm_onramp": _confirm_onramp,
        "submit_bank_details": _submit_bank_details,
        "confirm_bank_details": _confirm_bank_details,
        "submit_wallet_address": _submit_wallet_address,
        "check_deposit_status": _check_status,
        "check_payment_status": _check_status,
        "cancel_order": _cancel_order,
        "get_receipt": _get_receipt,
    }
    handler = handlers.get(tool_name)
    if not handler:
        logger.error("Unknown tool: %s", tool_name)
        return SAFE_FALLBACK
    return await handler(tool_args, order, session_id, provider, db, user)


# ─── Quotes (also transition state to *_QUOTING so confirm_* becomes allowed) ──

async def _get_offramp_quote(args, order, session_id, provider, db, user=None) -> str:
    q = await provider.get_offramp_quote(args["token"], float(args["amount"]), args["currency"])
    # Re-quote: if there's an existing order with no Paycrest order yet, update it in place.
    if order and not order.paycrest_order_id:
        await OrderRepository.update(
            db, order, direction="offramp", token=q.input_currency, amount=q.input_amount,
            currency=q.output_currency, rate=q.rate, output_amount=q.output_amount,
            status=OrderStatus.OFFRAMP_QUOTING,
        )
    else:
        await OrderRepository.create_quote(
            db, session_id, "offramp", q.input_currency, q.input_amount, q.output_currency,
            q.rate, q.output_amount, OrderStatus.OFFRAMP_QUOTING,
        )
    return json.dumps({
        "direction": "offramp",
        "rate": q.rate,
        "you_send": f"{q.input_amount} {q.input_currency}",
        "you_receive": f"{q.output_amount:,.2f} {q.output_currency}",
        "fee": f"{q.fee} {q.fee_currency}",
    })


async def _get_onramp_quote(args, order, session_id, provider, db, user=None) -> str:
    q = await provider.get_onramp_quote(args["token"], float(args["amount"]), args["currency"])
    if order and not order.paycrest_order_id:
        await OrderRepository.update(
            db, order, direction="onramp", token=q.output_currency, amount=q.output_amount,
            currency=q.input_currency, rate=q.rate, output_amount=q.input_amount,
            status=OrderStatus.ONRAMP_QUOTING,
        )
    else:
        await OrderRepository.create_quote(
            db, session_id, "onramp", q.output_currency, q.output_amount, q.input_currency,
            q.rate, q.input_amount, OrderStatus.ONRAMP_QUOTING,
        )
    return json.dumps({
        "direction": "onramp",
        "rate": q.rate,
        "you_pay": f"{q.input_amount:,.2f} {q.input_currency}",
        "you_receive": f"{q.output_amount} {q.output_currency}",
        "fee": f"{q.fee} {q.fee_currency}",
    })


# ─── Confirmations (move to COLLECTING_*) ──────────────────────────────────────

async def _confirm_offramp(args, order, session_id, provider, db, user=None) -> str:
    if not order:
        return SAFE_FALLBACK
    await OrderRepository.set_status(db, order, OrderStatus.OFFRAMP_COLLECTING_BANK)
    return json.dumps({"ok": True, "next": "collect_bank_details"})


async def _confirm_onramp(args, order, session_id, provider, db, user=None) -> str:
    if not order:
        return SAFE_FALLBACK
    await OrderRepository.set_status(db, order, OrderStatus.ONRAMP_COLLECTING_WALLET)
    return json.dumps({"ok": True, "next": "collect_wallet_address"})


# ─── Submissions (the ONLY place Paycrest orders are created) ──────────────────

async def _submit_bank_details(args, order, session_id, provider, db, user=None) -> str:
    """Resolve the bank, fetch + verify the account name, and store it — but do NOT
    create the order yet. The user must confirm the verified name first."""
    if not order:
        return SAFE_FALLBACK
    bank_name = args["bank_name"]
    account_number = args["account_number"]

    code = await provider.resolve_institution_code(order.currency, bank_name)
    if not code:
        return json.dumps({"error": f"Could not match '{bank_name}' to a supported bank for {order.currency}."})

    try:
        canonical = await provider.verify_bank_account(code, account_number)
    except Exception as e:  # noqa: BLE001
        logger.warning("verify-account failed: %s", e)
        return json.dumps({"error": "Could not verify that account number right now. Please double-check it and try again."})

    if not canonical:
        return json.dumps({"error": "That account number could not be verified. Please double-check it."})

    await OrderRepository.update(
        db, order,
        bank_name=bank_name, institution_code=code,
        account_number=account_number, account_name=canonical,
        status=OrderStatus.OFFRAMP_CONFIRMING_BANK,
    )
    return json.dumps({
        "verified_account_name": canonical,
        "bank": bank_name,
        "account_number": account_number,
    })


async def _confirm_bank_details(args, order, session_id, provider, db, user=None) -> str:
    """User confirmed the verified name — create the Paycrest order via the shared flow."""
    if not order or not order.institution_code:
        return SAFE_FALLBACK
    return json.dumps(await orders_flow.create_offramp(db, order, provider, session_id))


async def _submit_wallet_address(args, order, session_id, provider, db, user=None) -> str:
    """Create the onramp order. Uses the user's saved bank for that currency as the
    Paycrest-required refund account (same path as the buttons)."""
    if not order:
        return SAFE_FALLBACK
    refund = ("", "", "")
    if user:
        banks = await AccountRepository.list_banks(db, user.id, order.currency)
        if banks:
            b = banks[0]
            refund = (b.institution_code, b.account_number, b.account_name)
    return json.dumps(await orders_flow.create_onramp(
        db, order, provider, session_id, args["wallet_address"], args["network"], *refund
    ))


# ─── Status / cancel / receipt ─────────────────────────────────────────────────

async def _check_status(args, order, session_id, provider, db, user=None) -> str:
    if not order or not order.paycrest_order_id:
        return json.dumps({"status": "no_order"})
    # Live pull from Paycrest, then apply the same settlement logic the poller uses —
    # so asking "is it done?" can itself drive the 0G writes and state transition.
    data = await provider.get_order_status(order.paycrest_order_id)
    action = await apply_status(db, order, data)
    return json.dumps({
        "paycrest_status": data.get("status", "unknown"),
        "order_status": order.status.value,
        "action": action,
    })


async def _cancel_order(args, order, session_id, provider, db, user=None) -> str:
    if not order:
        return json.dumps({"ok": True})
    await OrderRepository.set_status(db, order, OrderStatus.CANCELLED)
    return json.dumps({"ok": True, "cancelled": True})


async def _get_receipt(args, order, session_id, provider, db, user=None) -> str:
    if not order:
        return json.dumps({"error": "no order"})
    return json.dumps({
        "status": order.status.value,
        "direction": order.direction,
        "amount": float(order.amount) if order.amount else None,
        "token": order.token,
        "currency": order.currency,
        "storage_hash": order.storage_hash,
        "registry_tx_hash": order.registry_tx_hash,
        "paycrest_order_id": order.paycrest_order_id,
    })
