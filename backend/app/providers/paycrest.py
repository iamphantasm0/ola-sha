import logging

import httpx

from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.base import (
    IFiatProvider,
    OrderResult,
    PaymentInstructions,
    QuoteResult,
)

logger = logging.getLogger(__name__)


class PaycrestProvider(IFiatProvider):
    """
    Paycrest Sender API v2.
    Docs: https://docs.paycrest.io/implementation-guides/sender-api-integration

    Both onramp and offramp go through POST /v2/sender/orders; direction is set
    by the source/destination types. Corridors: NGN, KES, UGX, TZS, MWK, BRL.

    IMPORTANT: Ola uses a SEPARATE sender account from Sterling Concierge —
    Paycrest allows one webhook URL per account.

    v2 gotchas handled here:
      • amount values are STRINGS, not numbers
      • do NOT pass `rate` on order create — let the API pick the best rate
      • refundAddress is nested under source (offramp)
      • institution CODES are required, not human-readable bank names
    """

    def __init__(self):
        self.base_url = settings.PAYCREST_BASE_URL.rstrip("/")
        self.network = settings.PAYCREST_DEFAULT_NETWORK
        self.headers = {
            "API-Key": settings.PAYCREST_API_KEY,
            "Content-Type": "application/json",
        }
        # currency -> [{name, code}, ...]; filled lazily and cached
        self._institutions: dict[str, list[dict]] = {}

    # ─── Rates (public endpoint — no API key needed) ────────────────────

    async def get_offramp_quote(
        self, token: str, amount: float, currency: str
    ) -> QuoteResult:
        data = await self._get_rate(token, amount, currency)
        sell = data.get("sell") or {}
        rate = float(sell.get("rate") or data.get("rate", 0) or 0)
        return QuoteResult(
            provider="paycrest",
            direction="offramp",
            input_amount=amount,
            input_currency=token,
            output_amount=round(amount * rate, 2),
            output_currency=currency,
            rate=rate,
            fee=float(sell.get("fee", 0) or 0),
            fee_currency=token,
            quote_id=None,
            expires_at=None,
        )

    async def get_onramp_quote(
        self, token: str, amount: float, currency: str
    ) -> QuoteResult:
        data = await self._get_rate(token, amount, currency)
        buy = data.get("buy") or {}
        rate = float(buy.get("rate") or data.get("rate", 0) or 0)
        fiat_needed = round(amount * rate, 2)
        return QuoteResult(
            provider="paycrest",
            direction="onramp",
            input_amount=fiat_needed,
            input_currency=currency,
            output_amount=amount,
            output_currency=token,
            rate=rate,
            fee=float(buy.get("fee", 0) or 0),
            fee_currency=currency,
            quote_id=None,
            expires_at=None,
        )

    async def _get_rate(self, token: str, amount: float, currency: str) -> dict:
        url = f"{self.base_url}/rates/{self.network}/{token}/{amount}/{currency}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url)
            r.raise_for_status()
            return r.json().get("data", {})

    # ─── Institutions + account verification ────────────────────────────

    async def get_institutions(self, currency: str) -> list[dict]:
        if currency in self._institutions:
            return self._institutions[currency]
        url = f"{self.base_url}/institutions/{currency}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, headers=self.headers)
            r.raise_for_status()
            items = r.json().get("data", []) or []
        self._institutions[currency] = items
        return items

    async def _resolve_institution(self, currency: str, bank_name: str) -> str:
        """Map a human bank name (e.g. 'GTBank') to its Paycrest code."""
        items = await self.get_institutions(currency)
        needle = bank_name.strip().lower()
        # exact, then substring, then token-overlap
        for it in items:
            if (it.get("name") or "").strip().lower() == needle:
                return it["code"]
        for it in items:
            name = (it.get("name") or "").lower()
            if needle in name or name in needle:
                return it["code"]
        for it in items:
            name = (it.get("name") or "").lower()
            if any(tok in name for tok in needle.split() if len(tok) > 2):
                return it["code"]
        raise ProviderError(
            f"Could not match bank '{bank_name}' to a {currency} institution code."
        )

    async def verify_bank_account(
        self, institution_code: str, account_identifier: str
    ) -> str:
        url = f"{self.base_url}/verify-account"
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                url,
                headers=self.headers,
                json={
                    "institution": institution_code,
                    "accountIdentifier": account_identifier,
                },
            )
            r.raise_for_status()
            return r.json().get("data", "") or ""

    # ─── Order creation ─────────────────────────────────────────────────

    async def create_offramp_order(
        self,
        token: str,
        amount: float,
        currency: str,
        bank_name: str,
        account_number: str,
        account_name: str,
        sender_id: str,
    ) -> OrderResult:
        """POST /v2/sender/orders — offramp (crypto -> fiat)."""
        institution_code = await self._resolve_institution(currency, bank_name)

        # Best-effort canonical name lookup (non-fatal if unavailable).
        canonical = ""
        try:
            canonical = await self.verify_bank_account(institution_code, account_number)
        except Exception as e:  # noqa: BLE001
            logger.warning("verify-account failed (continuing): %s", e)

        payload = {
            "amount": str(amount),  # string — v2 requirement
            "source": {
                "type": "crypto",
                "currency": token,
                "network": self.network,
                "refundAddress": settings.PAYCREST_REFUND_ADDRESS,
            },
            "destination": {
                "type": "fiat",
                "currency": currency,
                "recipient": {
                    "institution": institution_code,
                    "accountIdentifier": account_number,
                    "accountName": canonical or account_name,
                    "memo": f"Ola {sender_id[:8]}",
                },
            },
            "reference": f"zr-off-{sender_id[:12]}",
        }
        data = await self._create_order(payload)

        acct = data.get("providerAccount", {}) or {}
        return OrderResult(
            provider="paycrest",
            provider_order_id=data["id"],
            status=data.get("status", "initiated"),
            payment_instructions=PaymentInstructions(
                direction="offramp",
                deposit_address=acct.get("receiveAddress"),
                deposit_token=token,
                deposit_network=acct.get("network", self.network),
                valid_until=acct.get("validUntil"),
            ),
            raw=data,
        )

    async def create_onramp_order(
        self,
        token: str,
        amount: float,
        currency: str,
        wallet_address: str,
        network: str,
        sender_id: str,
        refund_institution: str = "",
        refund_account_number: str = "",
        refund_account_name: str = "",
    ) -> OrderResult:
        """POST /v2/sender/orders — onramp (fiat -> crypto)."""
        payload = {
            "amount": str(amount),
            "amountIn": "fiat",
            "source": {
                "type": "fiat",
                "currency": currency,
                "refundAccount": {
                    "institution": refund_institution or "GTBINGLA",
                    "accountIdentifier": refund_account_number or "0000000000",
                    "accountName": refund_account_name or "Ola Refund",
                },
            },
            "destination": {
                "type": "crypto",
                "currency": token,
                "recipient": {"address": wallet_address, "network": network},
            },
            "reference": f"zr-on-{sender_id[:12]}",
        }
        data = await self._create_order(payload)

        acct = data.get("providerAccount", {}) or {}
        return OrderResult(
            provider="paycrest",
            provider_order_id=data["id"],
            status=data.get("status", "initiated"),
            payment_instructions=PaymentInstructions(
                direction="onramp",
                bank_name=acct.get("institution"),
                account_number=acct.get("accountIdentifier"),
                account_name=acct.get("accountName"),
                amount_to_transfer=acct.get("amountToTransfer"),
                transfer_currency=acct.get("currency"),
                valid_until=acct.get("validUntil"),
            ),
            raw=data,
        )

    async def _create_order(self, payload: dict) -> dict:
        url = f"{self.base_url}/sender/orders"
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, headers=self.headers, json=payload)
            if r.status_code >= 400:
                logger.error("Paycrest order error %s: %s", r.status_code, r.text)
                raise ProviderError(f"Paycrest order failed ({r.status_code}): {r.text}")
            return r.json()["data"]

    # ─── Status polling ─────────────────────────────────────────────────

    async def get_order_status(self, provider_order_id: str) -> dict:
        url = f"{self.base_url}/sender/orders/{provider_order_id}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, headers=self.headers)
            r.raise_for_status()
            return r.json()["data"]
