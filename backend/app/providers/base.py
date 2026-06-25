from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class QuoteResult:
    provider: str
    direction: str          # "onramp" | "offramp"
    input_amount: float
    input_currency: str     # "USDT"/"USDC" (offramp) or "NGN"/... (onramp)
    output_amount: float
    output_currency: str
    rate: float             # local_currency per USD
    fee: float
    fee_currency: str
    quote_id: Optional[str]
    expires_at: Optional[str]


@dataclass
class PaymentInstructions:
    """What to show the user after order creation."""

    direction: str

    # Offramp: show deposit address
    deposit_address: Optional[str] = None
    deposit_token: Optional[str] = None
    deposit_network: Optional[str] = None

    # Onramp: show bank account to send fiat to
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    amount_to_transfer: Optional[str] = None
    transfer_currency: Optional[str] = None
    reference: Optional[str] = None

    # Both: deadline by which the user must act
    valid_until: Optional[str] = None


@dataclass
class OrderResult:
    provider: str
    provider_order_id: str
    status: str
    payment_instructions: PaymentInstructions
    raw: dict


class IFiatProvider(ABC):
    """
    Interface for fiat <-> stablecoin providers.
    Implement this to add Transak, Yellow Card, etc.
    """

    @abstractmethod
    async def get_offramp_quote(
        self, token: str, amount: float, currency: str
    ) -> QuoteResult:
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def get_onramp_quote(
        self, token: str, amount: float, currency: str
    ) -> QuoteResult:
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
