from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class QuoteResult:
    provider: str
    direction: str  # "onramp" | "offramp"
    input_amount: float
    input_currency: str  # "USDT"/"USDC" (offramp) or "NGN" (onramp)
    output_amount: float
    output_currency: str
    rate: float
    fee: float
    fee_currency: str
    quote_id: Optional[str] = None
    expires_at: Optional[str] = None


@dataclass
class PaymentInstructions:
    """What to show the user after order creation."""

    direction: str
    # Offramp: where the user sends stablecoin
    deposit_address: Optional[str] = None
    deposit_token: Optional[str] = None
    deposit_network: Optional[str] = None
    # Onramp: virtual bank account the user pays fiat into
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    amount_to_transfer: Optional[str] = None
    transfer_currency: Optional[str] = None
    reference: Optional[str] = None
    # Shared
    valid_until: Optional[str] = None


@dataclass
class OrderResult:
    provider: str
    provider_order_id: str
    status: str
    payment_instructions: PaymentInstructions
    raw: dict


class IFiatProvider(ABC):
    """Interface for fiat <-> stablecoin providers (Paycrest, Transak, etc.)."""

    @abstractmethod
    async def get_offramp_quote(self, token: str, amount: float, currency: str) -> QuoteResult:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def get_onramp_quote(self, token: str, amount: float, currency: str) -> QuoteResult:
        ...

    @abstractmethod
    async def create_onramp_order(
        self,
        token: str,
        amount: float,
        currency: str,
        wallet_address: str,
        network: str,
        sender_id: str,
    ) -> OrderResult:
        ...

    @abstractmethod
    async def get_order_status(self, provider_order_id: str) -> dict:
        ...

    @abstractmethod
    async def verify_bank_account(self, institution_code: str, account_identifier: str) -> str:
        ...

    @abstractmethod
    async def get_institutions(self, currency: str) -> list[dict]:
        ...

    @abstractmethod
    async def resolve_institution_code(self, currency: str, bank_name: str) -> Optional[str]:
        ...
