"""
The firewall: executes tool calls and enforces the state gate.

Every tool call is re-checked against TOOLS_BY_STATE here, server-side. Even if
the model is tricked into emitting a tool that isn't valid for the current
state, it is refused and logged. Real money movement (Paycrest order creation)
happens ONLY in submit_bank_details / submit_wallet_address. 0G Storage and
0G Chain writes happen ONLY in the webhook handler — never here.
"""

import json
import logging

from app.agent.tools import TOOLS_BY_STATE
from app.models.order import OrderStatus
from app.providers.base import IFiatProvider
from app.repositories.orders import OrderRepository

logger = logging.getLogger(__name__)

SAFE_FALLBACK = "I can't do that at this stage. Let's continue with your current step."


async def dispatch_tool_call(
    tool_name: str,
    tool_args: dict,
    current_state: str,
    order,
    session_id: str,
    provider: IFiatProvider,
    db_session,
) -> str:
    allowed = TOOLS_BY_STATE.get(current_state, [])
    if tool_name not in allowed:
        logger.warning(
            "BLOCKED tool call: %s in state %s (session=%s)",
            tool_name,
            current_state,
            session_id,
        )
        return SAFE_FALLBACK

    handlers = {
        "get_offramp_quote": _get_offramp_quote,
        "get_onramp_quote": _get_onramp_quote,
        "confirm_offramp": _confirm_offramp,
        "confirm_onramp": _confirm_onramp,
        "submit_bank_details": _submit_bank_details,
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

    try:
        return await handler(
            args=tool_args,
            order=order,
            session_id=session_id,
            provider=provider,
            db=db_session,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("Tool %s failed: %s", tool_name, e)
        return json.dumps(
            {"error": "Something went wrong processing that. Please try again."}
        )


# ─── Quotes ─────────────────────────────────────────────────────────────


async def _get_offramp_quote(*, args, session_id, provider, db, **_):
    await OrderRepository.cancel_active_for_session(db, session_id)
    quote = await provider.get_offramp_quote(
        token=args["token"], amount=args["amount"], currency=args["currency"]
    )
    order = await OrderRepository.create_quote(
        db,
        session_id=session_id,
        direction="offramp",
        token=quote.input_currency,
        amount=quote.input_amount,
        currency=quote.output_currency,
        rate=quote.rate,
        output_amount=quote.output_amount,
        status=OrderStatus.OFFRAMP_QUOTING,
    )
    return json.dumps(
        {
            "order_id": str(order.id),
            "you_sell": f"{quote.input_amount} {quote.input_currency}",
            "you_receive": f"{quote.output_amount:,.2f} {quote.output_currency}",
            "rate": f"1 {quote.input_currency} = {quote.rate:,.2f} {quote.output_currency}",
            "next": "Ask the user to confirm to proceed.",
        }
    )


async def _get_onramp_quote(*, args, session_id, provider, db, **_):
    await OrderRepository.cancel_active_for_session(db, session_id)
    quote = await provider.get_onramp_quote(
        token=args["token"], amount=args["amount"], currency=args["currency"]
    )
    order = await OrderRepository.create_quote(
        db,
        session_id=session_id,
        direction="onramp",
        token=quote.output_currency,
        amount=quote.output_amount,
        currency=quote.input_currency,
        rate=quote.rate,
        output_amount=quote.output_amount,
        status=OrderStatus.ONRAMP_QUOTING,
    )
    return json.dumps(
        {
            "order_id": str(order.id),
            "you_pay": f"{quote.input_amount:,.2f} {quote.input_currency}",
            "you_receive": f"{quote.output_amount} {quote.output_currency}",
            "rate": f"1 {quote.output_currency} = {quote.rate:,.2f} {quote.input_currency}",
            "next": "Ask the user to confirm to proceed.",
        }
    )


# ─── Confirmations ──────────────────────────────────────────────────────


async def _confirm_offramp(*, order, db, **_):
    if not order:
        return json.dumps({"error": "No active quote to confirm."})
    await OrderRepository.update_status(db, order.id, OrderStatus.OFFRAMP_COLLECTING_BANK)
    return json.dumps(
        {
            "status": "confirmed",
            "next": "Ask the user for: bank name, 10-digit account number, and account name.",
        }
    )


async def _confirm_onramp(*, order, db, **_):
    if not order:
        return json.dumps({"error": "No active quote to confirm."})
    await OrderRepository.update_status(
        db, order.id, OrderStatus.ONRAMP_COLLECTING_WALLET
    )
    return json.dumps(
        {
            "status": "confirmed",
            "next": "Ask the user for their wallet address and preferred network.",
        }
    )


# ─── Collect details + create the Paycrest order ────────────────────────


async def _submit_bank_details(*, args, order, session_id, provider, db, **_):
    if not order:
        return json.dumps({"error": "No active order."})

    result = await provider.create_offramp_order(
        token=order.token,
        amount=float(order.amount),
        currency=order.currency,
        bank_name=args["bank_name"],
        account_number=args["account_number"],
        account_name=args["account_name"],
        sender_id=session_id,
    )
    pi = result.payment_instructions

    order.bank_name = args["bank_name"]
    order.account_number = args["account_number"]
    order.account_name = args["account_name"]
    order.paycrest_order_id = result.provider_order_id
    order.deposit_address = pi.deposit_address
    order.valid_until = pi.valid_until
    order.status = OrderStatus.OFFRAMP_AWAITING_DEPOSIT
    await db.flush()

    return json.dumps(
        {
            "order_id": str(order.id),
            "deposit_address": pi.deposit_address,
            "send_exactly": f"{order.amount} {order.token}",
            "network": pi.deposit_network,
            "valid_until": pi.valid_until,
            "next": "Show the user the deposit address and amount. They send from their own wallet.",
        }
    )


async def _submit_wallet_address(*, args, order, session_id, provider, db, **_):
    if not order:
        return json.dumps({"error": "No active order."})

    result = await provider.create_onramp_order(
        token=order.token,
        amount=float(order.amount),
        currency=order.currency,
        wallet_address=args["wallet_address"],
        network=args["network"],
        sender_id=session_id,
    )
    pi = result.payment_instructions

    order.wallet_address = args["wallet_address"]
    order.network = args["network"]
    order.paycrest_order_id = result.provider_order_id
    order.pay_bank_name = pi.bank_name
    order.pay_account_number = pi.account_number
    order.pay_account_name = pi.account_name
    order.pay_amount = pi.amount_to_transfer
    order.valid_until = pi.valid_until
    order.status = OrderStatus.ONRAMP_AWAITING_PAYMENT
    await db.flush()

    return json.dumps(
        {
            "order_id": str(order.id),
            "pay_to_bank": pi.bank_name,
            "account_number": pi.account_number,
            "account_name": pi.account_name,
            "amount_to_transfer": f"{pi.amount_to_transfer} {pi.transfer_currency or order.currency}",
            "valid_until": pi.valid_until,
            "next": "Show the user the bank account and exact amount to transfer.",
        }
    )


# ─── Status checks (read-only) ──────────────────────────────────────────


async def _check_status(*, order, provider, **_):
    if not order or not order.paycrest_order_id:
        return json.dumps({"error": "No order to check yet."})
    status = await provider.get_order_status(order.paycrest_order_id)
    return json.dumps(
        {
            "paycrest_status": status.get("status"),
            "note": "Settlement and on-chain receipt are finalized automatically by the backend.",
        }
    )


# ─── Cancel + receipt ───────────────────────────────────────────────────


async def _cancel_order(*, order, db, **_):
    if not order:
        return json.dumps({"status": "nothing_to_cancel"})
    await OrderRepository.update_status(db, order.id, OrderStatus.CANCELLED)
    return json.dumps({"status": "cancelled"})


async def _get_receipt(*, args, session_id, db, order, **_):
    target = order
    if not target:
        target = await OrderRepository.get_latest_by_session(db, session_id)
    if not target:
        return json.dumps({"error": "No order found."})
    return json.dumps(
        {
            "order_id": str(target.id),
            "direction": target.direction,
            "amount": f"{target.amount} {target.token}",
            "currency": target.currency,
            "status": target.status.value,
            "storage_hash": target.storage_hash,
            "registry_tx_hash": target.registry_tx_hash,
            "storage_explorer": (
                f"https://storagescan-galileo.0g.ai/tx/{target.storage_hash}"
                if target.storage_hash
                else None
            ),
            "chain_explorer": (
                f"https://chainscan-galileo.0g.ai/tx/{target.registry_tx_hash}"
                if target.registry_tx_hash
                else None
            ),
        }
    )
