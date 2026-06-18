import logging
import uuid
from typing import Optional

import httpx

from app.core.config import settings
from app.providers.base import (
    IFiatProvider,
    OrderResult,
    PaymentInstructions,
    ProviderError,
    QuoteResult,
)

logger = logging.getLogger(__name__)


class PaycrestProvider(IFiatProvider):
    """
    Paycrest Sender API v2. Both onramp and offramp via POST /v2/sender/orders.
    Corridors: NGN, KES, UGX, TZS, MWK, BRL. Tokens: USDC, USDT.

    v2 gotchas baked in:
      - amounts are STRINGS, not numbers
      - do NOT pass `rate` on create (let API pick best rate)
      - refundAddress nested under source
      - webhook events + statuses are lowercase
      - use institution CODES, never human-readable bank names
    """

    BASE_URL = settings.PAYCREST_BASE_URL
    DEFAULT_NETWORK = "base"  # lowest fees, natively supported

    def __init__(self):
        self.headers = {
            "API-Key": settings.PAYCREST_API_KEY,
            "Content-Type": "application/json",
        }
        # currency -> list[{code, name}], populated lazily / at startup
        self._institutions: dict[str, list[dict]] = {}

    # ─── Rates (public endpoint — no API key) ────────────────────────────────

    async def get_offramp_quote(self, token: str, amount: float, currency: str) -> QuoteResult:
        data = await self._get_rates(token, amount, currency)
        sell = data.get("sell") or {}
        rate = float(sell.get("rate") or data.get("rate", 0))
        return QuoteResult(
            provider="paycrest",
            direction="offramp",
            input_amount=amount,
            input_currency=token,
            output_amount=round(amount * rate, 2),
            output_currency=currency,
            rate=rate,
            fee=float(sell.get("fee", 0)),
            fee_currency=token,
        )

    async def get_onramp_quote(self, token: str, amount: float, currency: str) -> QuoteResult:
        data = await self._get_rates(token, amount, currency)
        buy = data.get("buy") or {}
        rate = float(buy.get("rate") or data.get("rate", 0))
        return QuoteResult(
            provider="paycrest",
            direction="onramp",
            input_amount=round(amount * rate, 2),  # fiat needed
            input_currency=currency,
            output_amount=amount,
            output_currency=token,
            rate=rate,
            fee=float(buy.get("fee", 0)),
            fee_currency=currency,
        )

    async def _get_rates(self, token: str, amount: float, currency: str) -> dict:
        url = f"{self.BASE_URL}/rates/{self.DEFAULT_NETWORK}/{token}/{amount}/{currency}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()["data"]

    # ─── Institutions + account verification ─────────────────────────────────

    async def get_institutions(self, currency: str) -> list[dict]:
        if currency in self._institutions:
            return self._institutions[currency]
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/institutions/{currency}", headers=self.headers
            )
            resp.raise_for_status()
            items = resp.json().get("data", [])
        self._institutions[currency] = items
        return items

    _STOP = {"of", "for", "the", "and", "&"}
    _GENERIC = {
        "bank", "mfb", "plc", "microfinance", "merchant", "limited", "ltd",
        "nigeria", "ng",
    }

    @staticmethod
    def _norm(s: str) -> str:
        return "".join(c for c in s.lower() if c.isalnum())

    def _core(self, words: list[str]) -> set[str]:
        """Distinctive words: drop stopwords and generic banking terms."""
        return {w for w in words if w not in self._STOP and w not in self._GENERIC}

    async def resolve_institution_code(self, currency: str, bank_name: str) -> Optional[str]:
        """Match a human-typed bank name to a Paycrest institution code.

        Handles full names ("Zenith Bank"), partials ("Kuda Bank" -> Kuda Microfinance
        Bank), acronyms ("GTB", "UBA"), and the acronym+"bank" form ("GTBank").
        """
        items = await self.get_institutions(currency)
        nt = self._norm(bank_name)
        target_words = [self._norm(w) for w in bank_name.lower().split() if self._norm(w)]
        core_target = self._core(target_words)
        if not nt:
            return None

        best, best_score = None, 0
        for it in items:
            code = it.get("code", "")
            name = it.get("name", "")
            words = [self._norm(w) for w in name.lower().split() if self._norm(w)]
            nn = self._norm(name)

            initials_all = "".join(w[0] for w in words if w)
            sig_words = [w for w in words if w not in self._STOP]
            initials_sig = "".join(w[0] for w in sig_words if w)
            core_name = self._core(words)
            core_words_ordered = [w for w in sig_words if w not in self._GENERIC]
            initials_core = "".join(w[0] for w in core_words_ordered if w)

            score = 0
            if nt == self._norm(code):
                score = 1000
            elif nt == nn:
                score = 950
            elif len(nt) >= 2 and nt in {initials_all, initials_sig}:
                score = 900                                  # "GTB", "UBA"
            elif initials_core and nt == initials_core + "bank":
                score = 880                                  # "GTBank"
            elif core_target and core_target <= core_name:
                score = 860                                  # "Kuda Bank", "First Bank", "Guaranty Trust Bank"
            elif core_name and core_name <= core_target:
                score = 840                                  # user typed extra words
            elif len(nt) >= 3 and (nn.startswith(nt) or nt in nn):
                score = 800                                  # "Zenit", substrings
            elif core_target & core_name:
                score = 300 * len(core_target & core_name)   # partial distinctive overlap

            if score > best_score:
                best, best_score = code, score

        return best if best_score >= 300 else None

    async def verify_bank_account(self, institution_code: str, account_identifier: str) -> str:
        """Fetch the canonical account holder name. Retries transient 5xx/timeouts."""
        last_exc: Optional[Exception] = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(3):
                try:
                    resp = await client.post(
                        f"{self.BASE_URL}/verify-account",
                        headers=self.headers,
                        json={"institution": institution_code, "accountIdentifier": account_identifier},
                    )
                    if resp.status_code >= 500:
                        last_exc = httpx.HTTPStatusError(
                            f"{resp.status_code}", request=resp.request, response=resp
                        )
                        continue
                    resp.raise_for_status()
                    return resp.json().get("data", "")
                except (httpx.TimeoutException, httpx.TransportError) as e:
                    last_exc = e
        if last_exc:
            raise last_exc
        return ""

    # ─── Order creation ──────────────────────────────────────────────────────

    async def create_offramp_order(
        self,
        token: str,
        amount: float,
        currency: str,
        institution_code: str,
        account_number: str,
        account_name: str,
        sender_id: str,
    ) -> OrderResult:
        payload = {
            "amount": str(amount),  # STRING — v2 requirement
            "source": {
                "type": "crypto",
                "currency": token,
                "network": self.DEFAULT_NETWORK,
                "refundAddress": settings.PAYCREST_REFUND_ADDRESS,
            },
            "destination": {
                "type": "fiat",
                "currency": currency,
                "recipient": {
                    "institution": institution_code,
                    "accountIdentifier": account_number,
                    "accountName": account_name,
                    "memo": f"Ola {sender_id[:8]}",
                },
            },
            # Unique per order — Paycrest 400s on a duplicate reference.
            "reference": f"ola-off-{uuid.uuid4().hex[:16]}",
        }
        data = await self._create_order(payload)
        acct = data.get("providerAccount", {})
        return OrderResult(
            provider="paycrest",
            provider_order_id=data["id"],
            status=data["status"],
            payment_instructions=PaymentInstructions(
                direction="offramp",
                deposit_address=acct.get("receiveAddress"),
                deposit_token=token,
                deposit_network=acct.get("network", self.DEFAULT_NETWORK),
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
        payload = {
            "amount": str(amount),
            "amountIn": "fiat",
            "source": {
                "type": "fiat",
                "currency": currency,
                "refundAccount": {
                    "institution": refund_institution or "",
                    "accountIdentifier": refund_account_number or "",
                    "accountName": refund_account_name or "Ola Refund",
                },
            },
            "destination": {
                "type": "crypto",
                "currency": token,
                "recipient": {"address": wallet_address, "network": network},
            },
            "reference": f"ola-on-{uuid.uuid4().hex[:16]}",
        }
        data = await self._create_order(payload)
        acct = data.get("providerAccount", {})
        return OrderResult(
            provider="paycrest",
            provider_order_id=data["id"],
            status=data["status"],
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
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.BASE_URL}/sender/orders", headers=self.headers, json=payload
            )
            if resp.status_code >= 400:
                msg = ""
                try:
                    msg = resp.json().get("message", "")
                except Exception:  # noqa: BLE001
                    msg = resp.text[:200]
                logger.warning("Paycrest order create %s: %s", resp.status_code, msg)
                raise ProviderError(msg or f"Provider rejected the order ({resp.status_code}).")
            return resp.json()["data"]

    # ─── Status polling ──────────────────────────────────────────────────────

    async def get_order_status(self, provider_order_id: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/sender/orders/{provider_order_id}", headers=self.headers
            )
            resp.raise_for_status()
            return resp.json()["data"]
