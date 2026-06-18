"""Deterministic, money-safe rendering of tool results.

The model decides WHICH tool to call (intent), but it must never free-form the
money-critical specifics — deposit addresses, bank accounts, verified names, amounts.
Those are rendered here directly from the tool output, so the model can't hallucinate
them. Returns None only when there's nothing tool-specific to render (then the caller
falls back to a model reply).
"""

import json
from typing import Optional


def render_tool_reply(tool_name: str, result_str: str) -> Optional[str]:
    # dispatcher returns a plain string (not JSON) when it blocks a tool
    try:
        r = json.loads(result_str)
    except (json.JSONDecodeError, TypeError):
        return result_str or None

    if not isinstance(r, dict):
        return None

    # Any tool can return an error/refusal — surface it verbatim.
    if "error" in r:
        return r.get("message") or r.get("error")

    if tool_name == "get_offramp_quote":
        return (
            "Here's your quote:\n\n"
            f"You send: {r.get('you_send')}\n"
            f"You receive: {r.get('you_receive')}\n"
            f"Fee: {r.get('fee')}\n\n"
            "Choose where to receive your payout below — or just tell me a different amount."
        )

    if tool_name == "get_onramp_quote":
        return (
            "Here's your quote:\n\n"
            f"You pay: {r.get('you_pay')}\n"
            f"You receive: {r.get('you_receive')}\n"
            f"Fee: {r.get('fee')}\n\n"
            "Choose the wallet to receive your stablecoin below — or tell me a different amount."
        )

    if tool_name == "confirm_offramp":
        return (
            "Confirmed. ✅\n\n"
            "Now send me your **bank name** and **account number** and I'll set up the payout."
        )

    if tool_name == "confirm_onramp":
        return (
            "Confirmed. ✅\n\n"
            "Now send me your **wallet address** and the **network** "
            "(Base, Polygon, Arbitrum, Ethereum, or BNB)."
        )

    if tool_name == "submit_bank_details":
        # Name verified — confirmation happens via the buttons below.
        return (
            f"I verified this account:\n\n"
            f"Name: **{r.get('verified_account_name')}**\n"
            f"Bank: {r.get('bank')}\n"
            f"Account: {r.get('account_number')}\n\n"
            "Confirm below to get your deposit address."
        )

    if tool_name == "confirm_bank_details":
        valid = f"\nThis address is valid until {r['valid_until']}." if r.get("valid_until") else ""
        return (
            f"Paying out to **{r.get('verified_account_name')}** ({r.get('bank')}).\n\n"
            f"To complete your sell, send exactly **{r.get('send_exactly')}** on "
            f"**{r.get('deposit_network')}** to:\n\n"
            f"`{r.get('deposit_address')}`"
            f"{valid}\n\n"
            "Reply once you've sent it and I'll track the settlement."
        )

    if tool_name == "submit_wallet_address":
        valid = f"\nValid until {r['valid_until']}." if r.get("valid_until") else ""
        return (
            "Send exactly "
            f"**{r.get('amount_to_transfer')} {r.get('currency')}** to this account:\n\n"
            f"Bank: {r.get('pay_to_bank')}\n"
            f"Account: {r.get('account_number')}\n"
            f"Name: {r.get('account_name')}"
            f"{valid}\n\n"
            "Reply once you've sent it and I'll track the settlement."
        )

    if tool_name in ("check_deposit_status", "check_payment_status"):
        if r.get("order_status") == "SETTLED":
            return "Settled. ✅ Your transaction is complete — the receipt is recorded on 0G."
        return (
            f"Current status: **{r.get('paycrest_status', 'pending')}**.\n"
            "I'll keep checking and let you know the moment it settles."
        )

    if tool_name == "cancel_order":
        return "Your order has been cancelled. Want to start a new buy or sell?"

    if tool_name == "get_receipt":
        lines = ["Here's your receipt:", f"- Status: {r.get('status')}"]
        if r.get("amount"):
            lines.append(f"- {r.get('amount')} {r.get('token')} → {r.get('currency')}")
        if r.get("storage_hash"):
            lines.append(f"- 0G Storage: {r.get('storage_hash')}")
        if r.get("registry_tx_hash"):
            lines.append(f"- 0G Chain tx: {r.get('registry_tx_hash')}")
        return "\n".join(lines)

    return None
