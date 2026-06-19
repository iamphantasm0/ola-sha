"""Order-advancing logic shared by the AI dispatcher and the deterministic /action endpoint.

Keeping it here means a button click and an AI tool call run the exact same code — the
money-moving steps have one implementation.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.order import Order, OrderStatus
from app.providers.base import IFiatProvider, ProviderError
from app.repositories.accounts import AccountRepository
from app.repositories.orders import OrderRepository

logger = logging.getLogger(__name__)


async def resolve_onramp_refund(db: AsyncSession, user, currency: str) -> tuple[str, str, str]:
    """Refund bank for a buy. Prefer the user's own saved bank (refund goes back to them);
    otherwise the platform default from env, so anyone can buy with just a wallet."""
    if user:
        banks = await AccountRepository.list_banks(db, user.id, currency)
        if banks:
            b = banks[0]
            return (b.institution_code, b.account_number, b.account_name)
    return (
        settings.PAYCREST_ONRAMP_REFUND_INSTITUTION,
        settings.PAYCREST_ONRAMP_REFUND_ACCOUNT,
        settings.PAYCREST_ONRAMP_REFUND_NAME,
    )


async def stage_bank(
    db: AsyncSession,
    order: Order,
    provider: IFiatProvider,
    bank_name: str,
    account_number: str,
    *,
    institution_code: Optional[str] = None,
    account_name: Optional[str] = None,
) -> dict:
    """Resolve + verify the bank (or use a pre-verified saved account), store it on the
    order, and move to CONFIRMING_BANK. Returns the verified info or {"error": ...}."""
    code = institution_code or await provider.resolve_institution_code(order.currency, bank_name)
    if not code:
        return {"error": f"Could not match '{bank_name}' to a supported bank for {order.currency}."}

    name = account_name
    if not name:
        try:
            name = await provider.verify_bank_account(code, account_number)
        except Exception as e:  # noqa: BLE001
            logger.warning("verify-account failed: %s", e)
            return {"error": "Could not verify that account number right now. Please try again."}
        if not name:
            return {"error": "That account number could not be verified. Please double-check it."}

    await OrderRepository.update(
        db, order, bank_name=bank_name, institution_code=code,
        account_number=account_number, account_name=name,
        status=OrderStatus.OFFRAMP_CONFIRMING_BANK,
    )
    return {"verified_account_name": name, "bank": bank_name, "account_number": account_number}


async def create_offramp(db: AsyncSession, order: Order, provider: IFiatProvider, sender_id: str) -> dict:
    """Create the Paycrest offramp order from the staged bank details; -> AWAITING_DEPOSIT."""
    if not order.institution_code:
        return {"error": "No bank details on file. Please provide your bank and account number."}
    try:
        result = await provider.create_offramp_order(
            token=order.token, amount=float(order.amount), currency=order.currency,
            institution_code=order.institution_code, account_number=order.account_number,
            account_name=order.account_name, sender_id=sender_id,
        )
    except ProviderError as e:
        return {"error": f"Couldn't create the order: {e}"}
    pi = result.payment_instructions
    await OrderRepository.update(
        db, order, paycrest_order_id=result.provider_order_id,
        deposit_address=pi.deposit_address, status=OrderStatus.OFFRAMP_AWAITING_DEPOSIT,
    )
    return {
        "verified_account_name": order.account_name, "bank": order.bank_name,
        "account_number": order.account_number, "deposit_address": pi.deposit_address,
        "deposit_token": pi.deposit_token, "deposit_network": pi.deposit_network,
        "valid_until": pi.valid_until, "send_exactly": f"{order.amount} {order.token}",
    }


async def create_onramp(db: AsyncSession, order: Order, provider: IFiatProvider, sender_id: str,
                        wallet_address: str, network: str,
                        refund_institution: str, refund_account_number: str,
                        refund_account_name: str) -> dict:
    """Create the Paycrest onramp order; -> AWAITING_PAYMENT.

    Paycrest requires a valid refund bank (where fiat returns if delivery fails).
    """
    if not refund_institution or not refund_account_number:
        return {"error": "To buy, I need a bank account for refunds. Add one to your saved "
                         "accounts first (it's where funds return if the transfer fails)."}
    try:
        result = await provider.create_onramp_order(
            token=order.token, amount=float(order.amount),
            currency=order.currency, wallet_address=wallet_address, network=network, sender_id=sender_id,
            refund_institution=refund_institution, refund_account_number=refund_account_number,
            refund_account_name=refund_account_name,
        )
    except ProviderError as e:
        return {"error": f"Couldn't create the order: {e}"}
    pi = result.payment_instructions
    await OrderRepository.update(
        db, order, wallet_address=wallet_address, network=network,
        paycrest_order_id=result.provider_order_id, status=OrderStatus.ONRAMP_AWAITING_PAYMENT,
    )
    return {
        "pay_to_bank": pi.bank_name, "account_number": pi.account_number,
        "account_name": pi.account_name, "amount_to_transfer": pi.amount_to_transfer,
        "currency": pi.transfer_currency, "valid_until": pi.valid_until,
    }


async def cancel(db: AsyncSession, order: Order) -> dict:
    await OrderRepository.set_status(db, order, OrderStatus.CANCELLED)
    return {"ok": True, "cancelled": True}
