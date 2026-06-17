# Ola — AI-Powered Crypto ↔ Fiat Exchange
## Zero Cup 2026 · Full Build Scope for Claude Code
### "A Sterling Concierge demo by Vela Labs"
### Updated: June 17, 2026

---

## SECTION A — CLAUDE CODE DEV ENVIRONMENT SETUP
### Do this before anything else. Gives Claude Code native 0G knowledge.

### A1. Install 0G Agent Skills (gives Claude Code 14 built-in 0G skills)

```bash
# Clone into project root as .0g-skills
git clone https://github.com/0gfoundation/0g-agent-skills .0g-skills

# Copy CLAUDE.md to project root — Claude Code auto-detects this on next session
cp .0g-skills/CLAUDE.md ./CLAUDE.md
```

What this does: Claude Code reads `CLAUDE.md` on startup and gains built-in knowledge of
all 0G SDKs, patterns, and anti-patterns. No more guessing package names or endpoints.
The `compute-plus-storage` cross-layer skill directly matches the Ola architecture.

Skills included: upload-file, download-file, merkle-verification, streaming-chat,
text-to-image, speech-to-text, provider-discovery, account-management, fine-tuning,
deploy-contract, interact-contract, scaffold-project, storage-plus-chain, compute-plus-storage.

Reference patterns auto-loaded: NETWORK_CONFIG.md, STORAGE.md, COMPUTE.md, CHAIN.md,
SECURITY.md, TESTING.md.

GitHub: https://github.com/0gfoundation/0g-agent-skills

### A2. Install 0G-CC MCP Server (gives Claude Code live access to 0G during dev)

```bash
npm install -g @0gfoundation/0g-cc
```

Then add to Claude Code's MCP config (`~/.claude/mcp.json` or via `claude mcp add`):

```json
{
  "mcpServers": {
    "0g": {
      "command": "0g-cc",
      "env": {
        "PRIVATE_KEY": "your_testnet_private_key",
        "RPC_URL": "https://evmrpc-testnet.0g.ai",
        "STORAGE_INDEXER": "https://indexer-storage-testnet-turbo.0g.ai"
      }
    }
  }
}
```

What this does: Claude Code can now call 0G Storage and Compute directly during
development — upload test records, verify storage hashes, check compute availability —
without switching to another terminal. Live feedback while building.

npm: https://www.npmjs.com/package/@0gfoundation/0g-cc

### A3. Feed AI Context Doc to Claude Code

At the start of any Claude Code session, paste this URL or use `/fetch`:
```
https://docs.0g.ai/ai-context
```

This page is built specifically for AI coding assistants. Contains every network endpoint,
chain ID, contract address, and SDK example in one document. 0G Labs maintains it.

### A4. Recommended Prompt Templates (from build.0g.ai/zero-coding)

For 0G Storage integration:
```
Help me integrate 0G Storage for decentralized file storage. Use @0gfoundation/0g-ts-sdk
to upload files with the two-layer architecture (Log for immutable data, KV for mutable).
```

For 0G Compute integration:
```
Help me run AI inference on 0G Compute's decentralized GPU marketplace. Use the OpenAI
SDK-compatible API for drop-in replacement. Set up pay-per-use model with TEE support.
```

For 0G Chain contract:
```
Write a Solidity smart contract for 0G Chain (EVM-compatible, 11K TPS). Use Hardhat for
deployment. Network: testnet, chainId 16602, RPC https://evmrpc-testnet.0g.ai
```

Zero Coding hub: https://build.0g.ai/zero-coding

---

## 0. What We Are Building

A **web-based AI chat interface** that lets users in Africa and LATAM swap between
stablecoins (USDC/USDT) and local currency (NGN, KES, UGX, TZS, MWK, BRL) in both directions —
onramp (fiat → crypto) and offramp (crypto → fiat).

The AI from **0G Compute** drives the entire conversation and calls tools to execute the flow.
**Paycrest** handles all money movement. **0G Storage** writes an immutable audit record per transaction.
**0G Chain** holds a lightweight on-chain settlement log (OrderRegistry contract).

### Why This Wins

- Judges can use it in a browser — no Telegram, no wallet setup required for the demo
- 0G does real work across all three services (Compute + Storage + Chain)
- Paycrest gives instant real settlement on testnet with zero provider complexity
- Six corridors live on day 1 (Nigeria, Kenya, Uganda, Tanzania, Malawi, Brazil)
- Domain knowledge is deep — this team has shipped this product before

---

## 1. Confirmed Facts (Read These Before Writing Any Code)

### Paycrest
- **Onramp AND offramp** both live in Sender API v2
- **Single endpoint for both:** `POST https://api.paycrest.io/v2/sender/orders`
- **Direction set by payload:** `source.type: "crypto"` + `destination.type: "fiat"` = offramp; inverse = onramp
- **Rate endpoint (public, no auth):** `GET /v2/rates/{network}/{from}/{amount}/{to}` → `data.sell.rate` (offramp), `data.buy.rate` (onramp)
- **Account verify:** `POST /v2/verify-account` — validates bank account, returns canonical name
- **Institution codes:** `GET /v2/institutions/{currency}` — use these codes, NOT human-readable bank names
- **Amounts are strings in v2** — `"100"` not `100` (breaking change from v1)
- **DO NOT pass `rate`** on order create — let API pick best available rate
- **`refundAddress`** replaces v1's `returnAddress` — now nested under `source.refundAddress`
- **Webhook events** (v2, lowercase): `payment_order.deposited`, `payment_order.pending`, `payment_order.validated`, `payment_order.settling`, `payment_order.settled`, `payment_order.refunding`, `payment_order.refunded`, `payment_order.expired`
- **Webhook has `direction` field:** `"offramp"` or `"onramp"` — use this to route handling
- **Notify user at:** `payment_order.validated` (offramp — fiat confirmed) or `payment_order.pending` (onramp — fiat received)
- **Write 0G records at:** `payment_order.settled` (both directions — fully onchain)
- **Signature verification:** HMAC-SHA256, compare as lowercase hex strings — NOT raw bytes
- **Retries:** exponential backoff for 24 hours on non-2xx. Always return 200 after accepting.
- **Testing:** mainnet only, minimum $0.50 per order
- **One webhook URL per sender account** — Ola must use a SEPARATE account from Sterling Concierge
- **Corridors live:** NGN, KES, UGX, TZS, MWK, BRL
- **Tokens:** USDC, USDT, cNGN
- **Chains:** Ethereum, Base, Arbitrum, Polygon, BSC, Lisk, Celo, Scroll
- **Settlement:** < 30 seconds median for NGN
- **Fees:** Zero for senders. Protocol fee embedded in provider rate.
- Docs: https://docs.paycrest.io/implementation-guides/sender-api-integration

### 0G Compute Router
- OpenAI-compatible API — use Python `openai` SDK, just swap `base_url`
- Testnet endpoint: `https://router-api-testnet.integratenetwork.work/v1`
- Mainnet endpoint: `https://router-api.0g.ai/v1`
- Get API key: https://pc.testnet.0g.ai → Dashboard → API Keys
- Models list: https://docs.0g.ai/developer-hub/building-on-0g/compute-network/router/models
- Use `zai-org/GLM-5-FP8` for MVP (low cost, fast, supports tool calling)
- Docs: https://docs.0g.ai/developer-hub/building-on-0g/compute-network/router/quickstart

### 0G Storage
- TypeScript SDK: **`@0gfoundation/0g-ts-sdk`** (correct package — NOT `0g-storage-ts-sdk`)
- Also needs: `ethers` v6 (never v5)
- Requires a Node.js sidecar service — Python backend calls it via HTTP
- Testnet RPC: `https://evmrpc-testnet.0g.ai`
- Testnet indexer (turbo): `https://indexer-storage-testnet-turbo.0g.ai`
- Testnet explorer: https://storagescan-galileo.0g.ai
- Starter kit: https://github.com/0gfoundation/0g-storage-ts-starter-kit
- Docs: https://docs.0g.ai/developer-hub/building-on-0g/storage/sdk

### 0G Chain (OrderRegistry)
- EVM-compatible L1 — deploy Solidity with Hardhat
- Testnet name: **Galileo**
- Testnet RPC: `https://evmrpc-testnet.0g.ai`
- Testnet Chain ID: **`16602`** (was 16600 — corrected)
- Testnet explorer: https://chainscan-galileo.0g.ai
- Testnet storage explorer: https://storagescan-galileo.0g.ai
- Mainnet name: **Aristotle**
- Mainnet RPC: `https://evmrpc.0g.ai`
- Mainnet Chain ID: **`16661`**
- Mainnet explorer: https://chainscan.0g.ai
- Faucet: https://faucet.0g.ai (0.1 OG/day)
- Google Cloud faucet: https://cloud.google.com/application/web3/faucet/0g/galileo
- Docs: https://docs.0g.ai/developer-hub/building-on-0g/contracts-on-0g/deploy-contracts

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Ola Web UI                        │
│                    (Next.js 14)                          │
│                                                          │
│  ┌──────────────────────┐  ┌────────────────────────┐   │
│  │   Chat Window        │  │   Transaction Sidebar  │   │
│  │   AI conversation    │  │   Status + progress    │   │
│  │   message bubbles    │  │   Paycrest ref         │   │
│  │   input bar          │  │   0G storage hash      │   │
│  └──────────────────────┘  └────────────────────────┘   │
└───────────────────────┬─────────────────────────────────┘
                        │  POST /api/v1/chat
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Agent Layer                          │   │
│  │  - Loads conversation history from DB             │   │
│  │  - Loads current order state from DB              │   │
│  │  - Injects ONLY tools valid for current state     │   │
│  │  - Calls 0G Compute Router (OpenAI-compat)        │   │
│  │  - Dispatches tool calls (double-gated)           │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  Paycrest     │  │  0G Storage  │  │  0G Chain   │  │
│  │  Provider     │  │  Sidecar     │  │  Registry   │  │
│  │  (real money) │  │  (audit log) │  │  (on-chain) │  │
│  └───────────────┘  └──────────────┘  └─────────────┘  │
│                                                          │
│  PostgreSQL — order state + users + conversation history │
└─────────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
   Paycrest API          Node.js sidecar
   (onramp+offramp)      (0G Storage SDK)
```

### Data Flow — Offramp (crypto → fiat)

```
1. User: "sell 200 USDT for NGN"
2. AI calls get_offramp_quote(token="USDT", amount=200, currency="NGN")
   → backend: GET /v2/rates/base/USDT/200/NGN (public, no auth)
   → uses data.sell.rate for offramp
   → AI responds with formatted quote
3. User confirms
4. AI calls confirm_offramp()
   → state transitions to OFFRAMP_COLLECTING_BANK in DB
5. User provides bank details (name → AI collects, backend resolves institution code)
6. AI calls submit_bank_details(bank, account_number, account_name)
   → backend: POST /v2/verify-account (validate account + get canonical name)
   → backend: POST /v2/sender/orders { source: {type:"crypto"}, destination: {type:"fiat"} }
   → response: providerAccount.receiveAddress (where user sends USDT)
   → state transitions to OFFRAMP_AWAITING_DEPOSIT
   → AI shows user the deposit address + validUntil deadline
7. User sends USDT to receiveAddress from their own wallet
8. Paycrest fires payment_order.validated → backend updates state to OFFRAMP_PROCESSING
   → AI notifies: "Fiat payment confirmed, settlement completing"
9. Paycrest fires payment_order.settled → backend triggers:
   a. Write audit record to 0G Storage → get rootHash
   b. Log to 0G Chain OrderRegistry → get chain tx hash
   c. Update DB order status to SETTLED with both hashes
   d. Push status update to frontend
10. AI: "Your ₦316,000 has been sent to GTBank ****6789. Receipt: [0G hash]"
```

### Data Flow — Onramp (fiat → crypto)

```
1. User: "buy 100 USDT with NGN"
2. AI calls get_onramp_quote(token="USDT", amount=100, currency="NGN")
   → backend: GET /v2/rates/base/USDT/100/NGN (public, no auth)
   → uses data.buy.rate for onramp
   → AI responds with NGN amount needed (e.g. ₦159,000)
3. User confirms
4. AI calls confirm_onramp()
   → state transitions to ONRAMP_COLLECTING_WALLET
5. User provides wallet address + preferred network
6. AI calls submit_wallet_address(address, network)
   → backend: POST /v2/sender/orders { source: {type:"fiat", amountIn:"fiat"},
                                        destination: {type:"crypto"} }
   → response: providerAccount = {institution, accountIdentifier, accountName,
                                   amountToTransfer, currency, validUntil}
   → state transitions to ONRAMP_AWAITING_PAYMENT
   → AI shows user the virtual bank account to pay + exact amount + deadline
7. User sends NGN via bank transfer to providerAccount details
8. Paycrest fires payment_order.pending → backend updates state to ONRAMP_PROCESSING
   → AI notifies: "NGN received. Sending USDT to your wallet."
9. Paycrest fires payment_order.settled → backend triggers:
   a. Write audit record to 0G Storage → get rootHash
   b. Log to 0G Chain OrderRegistry → get chain tx hash
   c. Update DB order status to SETTLED
   d. Push status update to frontend
10. AI: "100 USDT sent to 0x1234... on Base. Receipt: [0G hash]"
```

---

## 3. Full State Machine

```python
class OrderStatus(enum.Enum):
    # Shared
    IDLE                    = "IDLE"
    CANCELLED               = "CANCELLED"
    FAILED                  = "FAILED"
    SETTLED                 = "SETTLED"

    # Offramp flow
    OFFRAMP_QUOTING         = "OFFRAMP_QUOTING"
    OFFRAMP_COLLECTING_BANK = "OFFRAMP_COLLECTING_BANK"
    OFFRAMP_AWAITING_DEPOSIT= "OFFRAMP_AWAITING_DEPOSIT"
    OFFRAMP_PROCESSING      = "OFFRAMP_PROCESSING"

    # Onramp flow
    ONRAMP_QUOTING          = "ONRAMP_QUOTING"
    ONRAMP_COLLECTING_WALLET= "ONRAMP_COLLECTING_WALLET"
    ONRAMP_AWAITING_PAYMENT = "ONRAMP_AWAITING_PAYMENT"
    ONRAMP_PROCESSING       = "ONRAMP_PROCESSING"
```

### State → Allowed Tools (the hardening layer)

```python
TOOLS_BY_STATE = {
    "IDLE": [
        "get_offramp_quote",
        "get_onramp_quote",
    ],

    # Offramp
    "OFFRAMP_QUOTING": [
        "confirm_offramp",
        "cancel_order",
    ],
    "OFFRAMP_COLLECTING_BANK": [
        "submit_bank_details",
        "cancel_order",
    ],
    "OFFRAMP_AWAITING_DEPOSIT": [
        "check_deposit_status",
        "cancel_order",
    ],
    "OFFRAMP_PROCESSING": [],       # AI cannot call anything. Backend is working.

    # Onramp
    "ONRAMP_QUOTING": [
        "confirm_onramp",
        "cancel_order",
    ],
    "ONRAMP_COLLECTING_WALLET": [
        "submit_wallet_address",
        "cancel_order",
    ],
    "ONRAMP_AWAITING_PAYMENT": [
        "check_payment_status",
        "cancel_order",
    ],
    "ONRAMP_PROCESSING": [],        # AI cannot call anything. Backend is working.

    # Terminal
    "SETTLED": [
        "get_receipt",
        "get_offramp_quote",        # allow starting a new tx
        "get_onramp_quote",
    ],
    "FAILED": [
        "get_receipt",
        "get_offramp_quote",
        "get_onramp_quote",
    ],
    "CANCELLED": [
        "get_offramp_quote",
        "get_onramp_quote",
    ],
}
```

---

## 4. Tool Definitions

All tools passed to 0G Compute Router in OpenAI function-calling format.
Only tools for the current state are injected into each API call.

```python
# backend/app/agent/tools.py

ALL_TOOLS = {

    "get_offramp_quote": {
        "type": "function",
        "function": {
            "name": "get_offramp_quote",
            "description": (
                "Get the current exchange rate and calculate payout for selling "
                "stablecoins for local currency. Call this when the user wants to sell "
                "USDC or USDT and receive fiat money."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "enum": ["USDC", "USDT"],
                        "description": "The stablecoin to sell.",
                    },
                    "amount": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 4999,
                        "description": "Amount of stablecoin to sell (USD value).",
                    },
                    "currency": {
                        "type": "string",
                        "enum": ["NGN", "KES", "UGX", "TZS", "MWK", "BRL"],
                        "description": "The local currency to receive. Default NGN if not specified.",
                    },
                },
                "required": ["token", "amount", "currency"],
            },
        },
    },

    "get_onramp_quote": {
        "type": "function",
        "function": {
            "name": "get_onramp_quote",
            "description": (
                "Get the current exchange rate and calculate cost for buying "
                "stablecoins with local currency. Call this when the user wants to buy "
                "USDC or USDT using cash or bank transfer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "enum": ["USDC", "USDT"],
                        "description": "The stablecoin to buy.",
                    },
                    "amount": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 4999,
                        "description": "Amount of stablecoin to buy (USD value).",
                    },
                    "currency": {
                        "type": "string",
                        "enum": ["NGN", "KES", "UGX", "TZS", "MWK", "BRL"],
                        "description": "The local currency to pay with.",
                    },
                },
                "required": ["token", "amount", "currency"],
            },
        },
    },

    "confirm_offramp": {
        "type": "function",
        "function": {
            "name": "confirm_offramp",
            "description": (
                "User has explicitly agreed to the offramp rate quote. "
                "Call ONLY after the user says yes, confirms, or clearly accepts. "
                "Do not call speculatively."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },

    "confirm_onramp": {
        "type": "function",
        "function": {
            "name": "confirm_onramp",
            "description": (
                "User has explicitly agreed to the onramp rate quote. "
                "Call ONLY after the user says yes, confirms, or clearly accepts."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },

    "submit_bank_details": {
        "type": "function",
        "function": {
            "name": "submit_bank_details",
            "description": (
                "Submit the user's Nigerian bank account details for receiving NGN payout. "
                "Only call when you have ALL three fields from the user."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "bank_name": {
                        "type": "string",
                        "description": "Name of the Nigerian bank (e.g. GTBank, Access, UBA, Zenith).",
                    },
                    "account_number": {
                        "type": "string",
                        "pattern": "^[0-9]{10}$",
                        "description": "10-digit Nigerian bank account number.",
                    },
                    "account_name": {
                        "type": "string",
                        "description": "Account holder name exactly as on the bank account.",
                    },
                },
                "required": ["bank_name", "account_number", "account_name"],
            },
        },
    },

    "submit_wallet_address": {
        "type": "function",
        "function": {
            "name": "submit_wallet_address",
            "description": (
                "Submit the user's wallet address for receiving stablecoins after onramp."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "wallet_address": {
                        "type": "string",
                        "pattern": "^0x[a-fA-F0-9]{40}$",
                        "description": "EVM wallet address starting with 0x.",
                    },
                    "network": {
                        "type": "string",
                        "enum": ["base", "polygon", "arbitrum", "ethereum", "bnb"],
                        "description": "Which chain to receive the stablecoin on.",
                    },
                },
                "required": ["wallet_address", "network"],
            },
        },
    },

    "check_deposit_status": {
        "type": "function",
        "function": {
            "name": "check_deposit_status",
            "description": (
                "Check whether the user's stablecoin deposit has been detected by Paycrest. "
                "Call when the user asks for a status update after being given deposit instructions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID from the current session.",
                    },
                },
                "required": ["order_id"],
            },
        },
    },

    "check_payment_status": {
        "type": "function",
        "function": {
            "name": "check_payment_status",
            "description": (
                "Check whether the user's NGN bank transfer has been received by Paycrest. "
                "Call when the user claims they have sent payment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID from the current session.",
                    },
                },
                "required": ["order_id"],
            },
        },
    },

    "cancel_order": {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": (
                "Cancel the current order. Call ONLY if the user explicitly asks to cancel. "
                "Do not cancel due to confusion or silence."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief reason for cancellation.",
                    },
                },
                "required": [],
            },
        },
    },

    "get_receipt": {
        "type": "function",
        "function": {
            "name": "get_receipt",
            "description": "Get the transaction receipt for the completed or failed order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                },
                "required": ["order_id"],
            },
        },
    },
}
```

---

## 5. Provider Abstraction

```python
# backend/app/providers/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class QuoteResult:
    provider: str
    direction: str              # "onramp" | "offramp"
    input_amount: float
    input_currency: str         # "USDT" or "NGN"
    output_amount: float
    output_currency: str        # "NGN" or "USDT"
    rate: float                 # local_currency / USD
    fee: float
    fee_currency: str
    quote_id: Optional[str]     # provider-specific quote reference
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
    reference: Optional[str] = None  # payment reference to include


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
        self,
        token: str,
        amount: float,
        currency: str,
    ) -> QuoteResult:
        """Get rate for stablecoin → fiat."""
        pass

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
        """Create offramp order. Returns deposit instructions."""
        pass

    @abstractmethod
    async def get_onramp_quote(
        self,
        token: str,
        amount: float,
        currency: str,
    ) -> QuoteResult:
        """Get rate for fiat → stablecoin."""
        pass

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
        """Create onramp order. Returns bank payment instructions."""
        pass

    @abstractmethod
    async def get_order_status(self, provider_order_id: str) -> dict:
        """Poll order status."""
        pass
```

```python
# backend/app/providers/paycrest.py

import httpx
from app.providers.base import IFiatProvider, QuoteResult, OrderResult, PaymentInstructions
from app.core.config import settings


class PaycrestProvider(IFiatProvider):
    """
    Paycrest Sender API v2.
    Docs: https://docs.paycrest.io/implementation-guides/sender-api-integration
    Both onramp and offramp via the same POST /v2/sender/orders endpoint.
    Corridors: NGN, KES, UGX, TZS, MWK, BRL
    IMPORTANT: Use a SEPARATE sender account from Sterling Concierge — one webhook
    URL per account. Ola gets its own API key and its own webhook URL.
    """

    BASE_URL = "https://api.paycrest.io/v2"

    # Default network — Base has lowest fees, Paycrest supports it natively
    DEFAULT_NETWORK = "base"

    # v2 status values are lowercase
    SETTLED_STATUSES   = {"settled"}
    VALIDATED_STATUSES = {"validated"}           # offramp: fiat confirmed by provider
    FAILED_STATUSES    = {"refunded", "expired"}

    def __init__(self):
        self.headers = {
            "API-Key": settings.PAYCREST_API_KEY,
            "Content-Type": "application/json",
        }

    # ─── Rates (public endpoint — no API key needed) ─────────────────────────

    async def get_offramp_quote(self, token: str, amount: float, currency: str) -> QuoteResult:
        """
        GET /v2/rates/{network}/{from}/{amount}/{to}
        Public endpoint — no auth. Use data.sell.rate for offramp.
        Example: GET /v2/rates/base/USDT/100/NGN
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/rates/{self.DEFAULT_NETWORK}/{token}/{amount}/{currency}",
            )
            response.raise_for_status()
            data = response.json()["data"]

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
            quote_id=None,          # v2 rates are not quote IDs — omit rate on order create
            expires_at=None,
        )

    async def get_onramp_quote(self, token: str, amount: float, currency: str) -> QuoteResult:
        """
        GET /v2/rates/{network}/{from}/{amount}/{to}
        Same endpoint. Use data.buy.rate for onramp.
        amount is in crypto units (e.g. 100 USDT). Output is fiat needed.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/rates/{self.DEFAULT_NETWORK}/{token}/{amount}/{currency}",
            )
            response.raise_for_status()
            data = response.json()["data"]

        buy = data.get("buy") or {}
        rate = float(buy.get("rate") or data.get("rate", 0))
        fiat_needed = round(amount * rate, 2)
        return QuoteResult(
            provider="paycrest",
            direction="onramp",
            input_amount=fiat_needed,
            input_currency=currency,
            output_amount=amount,
            output_currency=token,
            rate=rate,
            fee=float(buy.get("fee", 0)),
            fee_currency=currency,
            quote_id=None,
            expires_at=None,
        )

    # ─── Account verification ─────────────────────────────────────────────────

    async def verify_bank_account(
        self, institution_code: str, account_identifier: str
    ) -> str:
        """
        POST /v2/verify-account
        Returns canonical account name. Call before creating an offramp order
        to validate the bank account and get the exact name to pass to the order.
        institution_code: SWIFT/bank code e.g. "GTBINGLA" for GTBank Nigeria.
        Fetch full list: GET /v2/institutions/NGN (or KES, UGX, etc.)
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/verify-account",
                headers=self.headers,
                json={
                    "institution": institution_code,
                    "accountIdentifier": account_identifier,
                },
            )
            response.raise_for_status()
            result = response.json()

        # Returns the canonical name or "OK" if name lookup not available
        return result.get("data", "")

    async def get_institutions(self, currency: str) -> list[dict]:
        """
        GET /v2/institutions/{currency}
        Returns list of {code, name} for valid institution codes.
        Use to map human-readable bank names → institution codes.
        Cache this in memory at startup.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/institutions/{currency}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json().get("data", [])

    # ─── Order creation ───────────────────────────────────────────────────────

    async def create_offramp_order(
        self, token: str, amount: float, currency: str,
        institution_code: str,   # e.g. "GTBINGLA" — NOT the human-readable name
        account_number: str,
        account_name: str,
        sender_id: str,
    ) -> OrderResult:
        """
        POST /v2/sender/orders — offramp (crypto → fiat)
        source.type = "crypto", destination.type = "fiat"
        Do NOT pass rate — let API pick best available rate.
        Amount values must be strings in v2 (not numbers).
        Response providerAccount.receiveAddress = where user sends USDT.
        """
        payload = {
            "amount": str(amount),          # string, not float — v2 requirement
            "source": {
                "type": "crypto",
                "currency": token,           # "USDT" or "USDC"
                "network": self.DEFAULT_NETWORK,
                "refundAddress": settings.PAYCREST_REFUND_ADDRESS,
            },
            "destination": {
                "type": "fiat",
                "currency": currency,        # "NGN", "KES", etc.
                "recipient": {
                    "institution": institution_code,     # SWIFT code e.g. "GTBINGLA"
                    "accountIdentifier": account_number,
                    "accountName": account_name,
                    "memo": f"Ola {sender_id[:8]}",
                },
            },
            "reference": f"zr-off-{sender_id[:12]}",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/sender/orders",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()["data"]

        # providerAccount.receiveAddress = address user must send tokens to
        provider_acct = data.get("providerAccount", {})
        return OrderResult(
            provider="paycrest",
            provider_order_id=data["id"],
            status=data["status"],          # "initiated" on creation
            payment_instructions=PaymentInstructions(
                direction="offramp",
                deposit_address=provider_acct.get("receiveAddress"),
                deposit_token=token,
                deposit_network=provider_acct.get("network", self.DEFAULT_NETWORK),
                valid_until=provider_acct.get("validUntil"),
            ),
            raw=data,
        )

    async def create_onramp_order(
        self, token: str, amount: float, currency: str,
        wallet_address: str,
        network: str,
        sender_id: str,
        refund_institution: str = "",       # for fiat refunds if onramp fails
        refund_account_number: str = "",
        refund_account_name: str = "",
    ) -> OrderResult:
        """
        POST /v2/sender/orders — onramp (fiat → crypto)
        source.type = "fiat", destination.type = "crypto"
        amountIn: "fiat" when amount is expressed in fiat currency.
        Response providerAccount = virtual bank account user sends NGN to.
        """
        payload = {
            "amount": str(amount),
            "amountIn": "fiat",             # amount is in fiat (e.g. NGN 50000)
            "source": {
                "type": "fiat",
                "currency": currency,
                # refundAccount: where to return fiat if onramp fails
                "refundAccount": {
                    "institution": refund_institution or "GTBINGLA",
                    "accountIdentifier": refund_account_number or "0000000000",
                    "accountName": refund_account_name or "Ola Refund",
                },
            },
            "destination": {
                "type": "crypto",
                "currency": token,
                "recipient": {
                    "address": wallet_address,
                    "network": network,
                },
            },
            "reference": f"zr-on-{sender_id[:12]}",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/sender/orders",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()["data"]

        # providerAccount = virtual bank account details for the user to pay
        provider_acct = data.get("providerAccount", {})
        return OrderResult(
            provider="paycrest",
            provider_order_id=data["id"],
            status=data["status"],
            payment_instructions=PaymentInstructions(
                direction="onramp",
                bank_name=provider_acct.get("institution"),
                account_number=provider_acct.get("accountIdentifier"),
                account_name=provider_acct.get("accountName"),
                amount_to_transfer=provider_acct.get("amountToTransfer"),
                transfer_currency=provider_acct.get("currency"),
                valid_until=provider_acct.get("validUntil"),
            ),
            raw=data,
        )

    # ─── Status polling ───────────────────────────────────────────────────────

    async def get_order_status(self, provider_order_id: str) -> dict:
        """GET /v2/sender/orders/:id — poll order status."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/sender/orders/{provider_order_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()["data"]
```

---

## 6. Agent Core

```python
# backend/app/agent/client.py

from openai import AsyncOpenAI
from app.core.config import settings

# 0G Compute Router — OpenAI-compatible, just a different base_url
og_client = AsyncOpenAI(
    base_url=settings.OG_COMPUTE_BASE_URL,
    api_key=settings.OG_COMPUTE_API_KEY,
)
```

```python
# backend/app/agent/prompts.py

from app.models.order import Order, OrderStatus


def build_system_prompt(state: str, order: Order | None) -> str:

    corridors = "Nigeria (NGN), Kenya (KES), Uganda (UGX), Tanzania (TZS), Malawi (MWK), Brazil (BRL)"

    base = f"""You are Ola, an AI built by Vela Labs that helps users exchange between stablecoins and local currency.

You support:
- SELL (offramp): User sends USDC or USDT, receives local currency to their bank account
- BUY (onramp): User sends local currency via bank transfer, receives USDC or USDT to their wallet

Active corridors: {corridors}
Supported stablecoins: USDC, USDT
Transaction limits: $1 minimum, $4,999 maximum per transaction

HARD RULES — never break these:
1. Only call tools that are provided to you in this message. Do not mention tools that are not listed.
2. Never ask for wallet private keys, seed phrases, or passwords.
3. Never promise a specific settlement time. Say "typically under 30 seconds" for NGN.
4. Never discuss trading, prices, or investment advice.
5. If the user's request is unclear, ask one clarifying question. Do not guess.
6. Keep responses concise. No long paragraphs. Use line breaks for amounts and instructions.
7. Always confirm transaction details before asking the user to send any money.
8. Never call submit_bank_details or submit_wallet_address unless you have ALL required fields.
"""

    state_instructions = {
        "IDLE": (
            "The user has not started a transaction. "
            "Greet them, explain what you do, and help them start a buy or sell."
        ),
        "OFFRAMP_QUOTING": (
            f"You have presented a rate quote to the user. "
            f"Order details: {_order_summary(order)}. "
            "Wait for explicit confirmation (yes/confirm/proceed) or cancellation before calling any tool."
        ),
        "OFFRAMP_COLLECTING_BANK": (
            "You need the user's bank details to process their payout. "
            "Collect: bank name, 10-digit account number, and account name. "
            "Ask for all three in one message. Do not submit until you have all three."
        ),
        "OFFRAMP_AWAITING_DEPOSIT": (
            f"The user must deposit {_order_amount(order)} to the address provided. "
            "Remind them of the deposit address if they ask. "
            "Check status only when they say they have sent the funds."
        ),
        "OFFRAMP_PROCESSING": (
            "The deposit is confirmed. Settlement is in progress. "
            "Tell the user to wait. Do not call any tools."
        ),
        "ONRAMP_QUOTING": (
            f"You have presented a rate quote. Order: {_order_summary(order)}. "
            "Wait for explicit confirmation before proceeding."
        ),
        "ONRAMP_COLLECTING_WALLET": (
            "Collect the user's wallet address and preferred network "
            "(Base, Polygon, Arbitrum, Ethereum, or BNB Chain)."
        ),
        "ONRAMP_AWAITING_PAYMENT": (
            "The user must send local currency to the bank account provided. "
            "Include the payment reference they must use. "
            "Check status only when they confirm payment has been sent."
        ),
        "ONRAMP_PROCESSING": (
            "Payment received. Stablecoin transfer is in progress. Tell user to wait."
        ),
        "SETTLED": (
            "Transaction complete. Offer receipt or help them start another transaction."
        ),
        "FAILED": (
            "Transaction failed. Offer to show receipt and help them start a new one."
        ),
        "CANCELLED": (
            "Order was cancelled. Offer to help them start a new transaction."
        ),
    }

    context = state_instructions.get(state, "Help the user with their transaction.")
    return f"{base}\nCURRENT STATE: {state}\nINSTRUCTION: {context}"


def _order_summary(order: Order | None) -> str:
    if not order:
        return "none"
    return f"{order.amount} {order.token} → {order.currency} (ID: {str(order.id)[:8]})"


def _order_amount(order: Order | None) -> str:
    if not order:
        return "the stablecoin amount"
    return f"{order.amount} {order.token}"
```

```python
# backend/app/agent/dispatcher.py
# The firewall — executes tool calls, enforces state gate

import json
import logging
from app.agent.tools import TOOLS_BY_STATE
from app.providers.base import IFiatProvider
from app.services.storage import store_transaction_record
from app.services.registry import log_to_chain

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
    """
    Execute a tool call from the AI.
    ALWAYS check state gate first — if tool not in allowed list, refuse and log.
    """
    allowed = TOOLS_BY_STATE.get(current_state, [])

    if tool_name not in allowed:
        logger.warning(
            f"BLOCKED tool call: {tool_name} in state {current_state} "
            f"(session={session_id})"
        )
        return SAFE_FALLBACK

    match tool_name:
        case "get_offramp_quote":
            return await _tool_get_offramp_quote(tool_args, session_id, provider, db_session)

        case "get_onramp_quote":
            return await _tool_get_onramp_quote(tool_args, session_id, provider, db_session)

        case "confirm_offramp":
            return await _tool_confirm_offramp(order, db_session)

        case "confirm_onramp":
            return await _tool_confirm_onramp(order, db_session)

        case "submit_bank_details":
            return await _tool_submit_bank_details(tool_args, order, session_id, provider, db_session)

        case "submit_wallet_address":
            return await _tool_submit_wallet_address(tool_args, order, session_id, provider, db_session)

        case "check_deposit_status":
            return await _tool_check_deposit_status(tool_args, order, provider, db_session)

        case "check_payment_status":
            return await _tool_check_payment_status(tool_args, order, provider, db_session)

        case "cancel_order":
            return await _tool_cancel_order(order, db_session)

        case "get_receipt":
            return await _tool_get_receipt(tool_args, db_session)

        case _:
            logger.error(f"Unknown tool: {tool_name}")
            return SAFE_FALLBACK


# --- individual tool implementations below ---
# Each function does ONE thing and transitions ONE state in the DB.
# Paycrest calls only happen in submit_bank_details and submit_wallet_address.
# 0G Storage and 0G Chain writes happen ONLY in the webhook handler, not here.

async def _tool_get_offramp_quote(args, session_id, provider, db):
    quote = await provider.get_offramp_quote(
        token=args["token"],
        amount=args["amount"],
        currency=args["currency"],
    )
    # Save pending quote to DB for this session
    # ... OrderRepository.create_pending(db, session_id, quote)
    return json.dumps({
        "rate": quote.rate,
        "input": f"{quote.input_amount} {quote.input_currency}",
        "output": f"{quote.output_amount:,.2f} {quote.output_currency}",
        "fee": f"{quote.fee} {quote.fee_currency}",
    })

# ... (similar pattern for all other tools)
```

---

## 7. 0G Services Implementation

### 7.1 Storage Sidecar (Node.js)

Identical to previous scope doc. Thin Express wrapper around 0G Storage TS SDK.

```
POST /store   { record: object }  → { rootHash: string }
GET  /record/:rootHash            → { data: object }
```

Called by backend after Paycrest webhook confirms settlement.

Record written per order:
```json
{
  "order_id": "uuid",
  "session_id": "uuid",
  "direction": "offramp",
  "token": "USDT",
  "amount": 200,
  "currency": "NGN",
  "output_amount": 316000,
  "rate": 1580,
  "paycrest_order_id": "PAY_XYZ",
  "status": "SETTLED",
  "settled_at": "2026-06-20T12:00:00Z",
  "product": "Ola — a Sterling Concierge demo by Vela Labs",
  "version": "1.0.0"
}
```

### 7.2 OrderRegistry Contract (0G Chain)

Minimal Solidity. Append-only log. 20 lines.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract OlaRegistry is Ownable {

    struct Settlement {
        string  direction;      // "onramp" | "offramp"
        string  currency;       // "NGN", "KES", etc.
        uint256 amount;         // in USD cents (200 USDT = 20000)
        string  storageHash;    // 0G Storage root hash of the audit record
        uint256 settledAt;      // block.timestamp
    }

    mapping(bytes32 => Settlement) public settlements;
    bytes32[] public allOrderIds;

    event OrderSettled(
        bytes32 indexed orderId,
        string direction,
        string currency,
        uint256 amount,
        string storageHash
    );

    constructor(address _owner) Ownable(_owner) {}

    /**
     * @notice Log a completed settlement. Called by backend wallet after Paycrest confirms.
     * @param orderId     keccak256 of our internal order UUID
     * @param direction   "onramp" or "offramp"
     * @param currency    fiat currency code
     * @param amount      USD value in cents
     * @param storageHash 0G Storage root hash of the full audit record
     */
    function logSettlement(
        bytes32 orderId,
        string calldata direction,
        string calldata currency,
        uint256 amount,
        string calldata storageHash
    ) external onlyOwner {
        require(settlements[orderId].settledAt == 0, "Already logged");

        settlements[orderId] = Settlement({
            direction:   direction,
            currency:    currency,
            amount:      amount,
            storageHash: storageHash,
            settledAt:   block.timestamp,
        });

        allOrderIds.push(orderId);
        emit OrderSettled(orderId, direction, currency, amount, storageHash);
    }

    function getSettlement(bytes32 orderId) external view returns (Settlement memory) {
        return settlements[orderId];
    }

    function totalSettlements() external view returns (uint256) {
        return allOrderIds.length;
    }
}
```

### 7.3 Webhook Handler — Where 0G Storage + Chain Get Called

```python
# backend/app/api/v1/webhooks.py
#
# Paycrest v2 webhook events (webhookVersion: "2"):
#   payment_order.deposited  → offramp: stablecoin deposit detected
#   payment_order.pending    → onramp: fiat deposit confirmed by provider
#   payment_order.validated  → offramp: fiat payout confirmed by provider ← notify user HERE
#   payment_order.settling   → onchain release in progress
#   payment_order.settled    → order complete ← write 0G records HERE
#   payment_order.refunding  → refund in progress
#   payment_order.refunded   → funds returned
#   payment_order.expired    → no deposit received before validUntil

from fastapi import APIRouter, Request, HTTPException, Depends
from app.services.storage import store_transaction_record
from app.services.registry import log_to_registry
from app.repositories.orders import OrderRepository
from app.models.order import OrderStatus
from app.core.dependencies import get_db
from app.core.config import settings
import hmac, hashlib, json

router = APIRouter()


def _verify_paycrest_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """
    v2 signature verification.
    Paycrest sends X-Paycrest-Signature as a hex string (64 chars).
    Compare as hex strings (lowercase), NOT as raw digest bytes.
    Use timing-safe equality on UTF-8 bytes of the hex strings.
    """
    sig = (signature or "").strip().lower()
    if not sig:
        return False
    computed = hmac.new(
        secret.strip().encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest().lower()
    if len(computed) != len(sig):
        return False
    return hmac.compare_digest(
        computed.encode("utf-8"),
        sig.encode("utf-8"),
    )


@router.post("/webhooks/paycrest")
async def paycrest_webhook(request: Request, db=Depends(get_db)):
    """
    Receives Paycrest v2 webhook events.
    Raw body must be read before JSON parsing — signature is over raw bytes.
    Returns 200 immediately after accepted to stop Paycrest retries.
    
    Paycrest retries exponentially for 24 hours on non-2xx. Always return 200
    even if we've already processed the event (idempotency via DB check).
    """
    raw_body = await request.body()

    # 1. Verify signature
    sig = request.headers.get("X-Paycrest-Signature", "")
    if not _verify_paycrest_signature(raw_body, sig, settings.PAYCREST_WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(raw_body)
    event          = payload.get("event", "")           # "payment_order.settled" etc.
    webhook_ver    = payload.get("webhookVersion", "1")
    data           = payload.get("data", {})
    paycrest_id    = data.get("id", "")
    direction      = data.get("direction", "")          # "offramp" | "onramp" (v2)
    status         = data.get("status", "")             # lowercase in v2

    order = await OrderRepository.get_by_paycrest_id(db, paycrest_id)
    if not order:
        return {"ok": True}     # not our order, acknowledge and move on

    # 2. Handle events
    if event == "payment_order.validated" and direction == "offramp":
        # Fiat confirmed by provider — safe to notify user that NGN is on the way
        # No 0G writes yet (not fully settled onchain)
        await OrderRepository.update_status(db, order.id, OrderStatus.OFFRAMP_PROCESSING)
        await push_status_update(order.session_id, {
            "event": "validated",
            "message": "Fiat payment confirmed. Settlement completing onchain.",
        })

    elif event == "payment_order.pending" and direction == "onramp":
        # Fiat deposit confirmed by provider — crypto release in progress
        await OrderRepository.update_status(db, order.id, OrderStatus.ONRAMP_PROCESSING)
        await push_status_update(order.session_id, {
            "event": "pending",
            "message": "Your fiat deposit was received. Sending USDT to your wallet.",
        })

    elif event == "payment_order.settled":
        # Order fully complete — write to 0G Storage and 0G Chain
        # Idempotency: skip if already settled
        if order.status == OrderStatus.SETTLED:
            return {"ok": True}

        # 3. Write immutable audit record to 0G Storage
        record = {
            "order_id":         str(order.id),
            "direction":        direction,
            "token":            order.token,
            "amount":           float(order.amount),
            "currency":         order.currency,
            "rate":             float(order.rate) if order.rate else None,
            "paycrest_order_id": paycrest_id,
            "tx_hash":          data.get("txHash"),     # onchain tx from Paycrest
            "event":            event,
            "status":           status,
            "settled_at":       data.get("updatedAt"),
            "product":          "Ola — a Sterling Concierge demo by Vela Labs",
            "version":          "1.0.0",
        }
        storage_hash = await store_transaction_record(record)

        # 4. Log to 0G Chain OrderRegistry (append-only, proves settlement onchain)
        order_id_bytes32 = hashlib.sha256(str(order.id).encode("utf-8")).digest()
        chain_tx = await log_to_registry(
            order_id_bytes=order_id_bytes32,
            direction=direction,
            currency=order.currency,
            amount_cents=int(float(order.amount) * 100),
            storage_hash=storage_hash,
        )

        # 5. Update DB with both 0G references
        await OrderRepository.settle(
            db, order.id,
            storage_hash=storage_hash,
            registry_tx_hash=chain_tx,
        )

        # 6. Push final status to frontend
        await push_status_update(order.session_id, {
            "event": "settled",
            "status": "SETTLED",
            "storage_hash": storage_hash,
            "chain_tx": chain_tx,
            "message": "Transaction complete.",
        })

    elif event in ("payment_order.refunded", "payment_order.expired"):
        await OrderRepository.update_status(db, order.id, OrderStatus.FAILED)
        await push_status_update(order.session_id, {
            "event": event.split(".")[1],
            "message": "Transaction failed. Your funds will be returned." if event == "payment_order.refunded" else "Transaction expired.",
        })

    return {"ok": True}
```

---

## 8. Database Models

```python
# backend/app/models/order.py

class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    session_id        = Column(UUID, ForeignKey("sessions.id"), nullable=False, index=True)
    direction         = Column(String(10), nullable=False)   # "onramp" | "offramp"
    token             = Column(String(10), nullable=False)   # "USDC" | "USDT"
    amount            = Column(Numeric(18, 6), nullable=False)
    currency          = Column(String(5), nullable=False)    # "NGN", "KES", etc.
    rate              = Column(Numeric(12, 4), nullable=True)
    output_amount     = Column(Numeric(18, 2), nullable=True)

    # Paycrest
    paycrest_order_id = Column(String(100), nullable=True, unique=True, index=True)

    # 0G references
    storage_hash      = Column(String(200), nullable=True)   # 0G Storage root hash
    registry_tx_hash  = Column(String(66), nullable=True)    # 0G Chain tx hash

    # State
    status            = Column(SAEnum(OrderStatus), nullable=False, default=OrderStatus.IDLE)

    # Offramp bank details (store hashed in production)
    bank_name         = Column(String(100), nullable=True)
    account_number    = Column(String(20), nullable=True)
    account_name      = Column(String(200), nullable=True)

    # Onramp wallet details
    wallet_address    = Column(String(42), nullable=True)
    network           = Column(String(20), nullable=True)


class Session(Base, TimestampMixin):
    """One browser session = one chat thread."""
    __tablename__ = "sessions"

    orders      = relationship("Order", back_populates="session")
    # No user login for MVP — anonymous sessions


class ConversationMessage(Base, TimestampMixin):
    """Chat history per session for AI context window."""
    __tablename__ = "conversation_messages"

    session_id  = Column(UUID, ForeignKey("sessions.id"), nullable=False, index=True)
    role        = Column(String(20), nullable=False)    # "user" | "assistant" | "tool"
    content     = Column(Text, nullable=False)
    tool_name   = Column(String(100), nullable=True)    # if role == "tool"
```

---

## 9. Frontend (Next.js 14)

### Design

- Dark theme. Clean. Crypto-native feel.
- Left column: full-height chat window
- Right column (240px): transaction status sidebar — shows current state, amounts, Paycrest ref, storage hash when settled
- Top bar: Ola logo + "New Chat" button
- No login/auth for MVP — session-based (UUID in localStorage)
- Mobile responsive

### Key Files

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout, dark theme globals
│   ├── page.tsx                # Main split-pane layout
│   └── api/
│       └── chat/
│           └── route.ts        # API route → proxies POST to FastAPI /api/v1/chat
├── components/
│   ├── Chat/
│   │   ├── ChatWindow.tsx      # Message list + input bar
│   │   ├── MessageBubble.tsx   # User vs AI bubble styles
│   │   └── InputBar.tsx        # Text input + send button
│   ├── Sidebar/
│   │   ├── StatusPanel.tsx     # Current order state display
│   │   ├── ReceiptCard.tsx     # Storage hash + Paycrest ref when settled
│   │   └── CurrencyBadge.tsx   # NGN/KES/etc flag + code
│   └── ui/                     # shadcn/ui components
├── lib/
│   ├── api.ts                  # fetch wrapper for FastAPI
│   ├── types.ts                # ChatMessage, OrderState, etc.
│   └── session.ts              # getSessionId() — creates UUID if not in localStorage
└── hooks/
    └── useChat.ts              # manages messages[], loading, sends to API
```

### Chat API Route

```typescript
// frontend/app/api/chat/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { message, sessionId } = body;

  const response = await fetch(
    `${process.env.BACKEND_URL}/api/v1/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    }
  );

  const data = await response.json();
  return NextResponse.json(data);
}
```

### Backend Chat Endpoint

```python
# backend/app/api/v1/chat.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.agent.client import og_client
from app.agent.tools import ALL_TOOLS, TOOLS_BY_STATE
from app.agent.prompts import build_system_prompt
from app.agent.dispatcher import dispatch_tool_call
from app.repositories.orders import OrderRepository
from app.repositories.conversations import ConversationRepository
from app.providers.paycrest import PaycrestProvider
from app.core.config import settings

router = APIRouter()
provider = PaycrestProvider()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    order_state: dict | None = None
    tool_called: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db=Depends(get_db)):
    # 1. Get or create session, load active order
    order = await OrderRepository.get_active_by_session(db, req.session_id)
    current_state = order.status.value if order else "IDLE"

    # 2. Load last N messages for context window
    history = await ConversationRepository.get_history(
        db, req.session_id, limit=20
    )

    # 3. Save user message to DB
    await ConversationRepository.add_message(
        db, req.session_id, role="user", content=req.message
    )

    # 4. Inject only tools valid for current state
    allowed_tool_names = TOOLS_BY_STATE.get(current_state, [])
    tools = [ALL_TOOLS[name] for name in allowed_tool_names] or None

    # 5. Call 0G Compute Router
    messages = [
        {"role": "system", "content": build_system_prompt(current_state, order)},
        *history,
        {"role": "user", "content": req.message},
    ]

    response = await og_client.chat.completions.create(
        model=settings.OG_COMPUTE_MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto" if tools else None,
        max_tokens=500,
        temperature=0.2,
    )

    choice = response.choices[0]
    tool_called = None

    if choice.finish_reason == "tool_calls":
        tool_call = choice.message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        tool_called = tool_name

        # 6. Dispatch through firewall
        tool_result = await dispatch_tool_call(
            tool_name=tool_name,
            tool_args=tool_args,
            current_state=current_state,
            order=order,
            session_id=req.session_id,
            provider=provider,
            db_session=db,
        )

        # 7. Second 0G call with tool result to get final reply
        messages.append(choice.message.model_dump())
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": tool_result,
        })

        followup = await og_client.chat.completions.create(
            model=settings.OG_COMPUTE_MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0.2,
        )
        reply = followup.choices[0].message.content

    else:
        reply = choice.message.content

    # 8. Save assistant reply to conversation history
    await ConversationRepository.add_message(
        db, req.session_id, role="assistant", content=reply
    )

    # 9. Reload order for state in response
    order = await OrderRepository.get_active_by_session(db, req.session_id)
    order_state = {
        "status": order.status.value,
        "direction": order.direction,
        "amount": float(order.amount) if order.amount else None,
        "token": order.token,
        "currency": order.currency,
        "storage_hash": order.storage_hash,
        "paycrest_order_id": order.paycrest_order_id,
    } if order else None

    return ChatResponse(
        reply=reply,
        order_state=order_state,
        tool_called=tool_called,
    )
```

---

## 10. Full Repository Structure

```
ola/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── chat.py           # POST /chat — main endpoint
│   │   │       ├── orders.py         # GET /orders/:id (for status polling)
│   │   │       └── webhooks.py       # POST /webhooks/paycrest
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── client.py             # 0G Compute Router client
│   │   │   ├── prompts.py            # System prompts by state
│   │   │   ├── tools.py              # Tool definitions + TOOLS_BY_STATE
│   │   │   └── dispatcher.py         # Tool execution + state gate
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # IFiatProvider ABC
│   │   │   └── paycrest.py           # PaycrestProvider
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── storage.py            # calls Node.js storage sidecar
│   │   │   └── registry.py           # calls 0G Chain OrderRegistry via web3.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── orders.py
│   │   │   ├── sessions.py
│   │   │   └── conversations.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── order.py
│   │   │   ├── session.py
│   │   │   └── conversation.py
│   │   ├── schemas/
│   │   │   ├── chat.py
│   │   │   └── order.py
│   │   └── core/
│   │       ├── config.py
│   │       ├── dependencies.py
│   │       └── exceptions.py
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── alembic.ini
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
│
├── storage-sidecar/                  # Node.js — 0G Storage SDK wrapper
│   ├── src/
│   │   ├── index.ts
│   │   ├── routes/storage.ts
│   │   └── lib/zg.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── contracts/                        # Solidity + Hardhat
│   ├── contracts/
│   │   └── OlaRegistry.sol
│   ├── scripts/
│   │   └── deploy.ts
│   ├── test/
│   │   └── OlaRegistry.test.ts
│   ├── hardhat.config.ts
│   └── package.json
│
├── frontend/                         # Next.js 14 chat UI
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   └── api/chat/route.ts
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── InputBar.tsx
│   │   └── Sidebar/
│   │       ├── StatusPanel.tsx
│   │       └── ReceiptCard.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── session.ts
│   ├── hooks/
│   │   └── useChat.ts
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
│
├── CLAUDE.md                             # 0G agent skills auto-loader (copy from .0g-skills)
├── .0g-skills/                           # 0G agent skills (git clone, not committed)
│   └── (14 skills + 6 patterns — gitignore this dir)
├── docker-compose.yml
├── docker-compose.override.yml
├── .env.example
└── README.md
```

---

## 11. Environment Variables

```dotenv
# ─── 0G COMPUTE ────────────────────────────────────────────────
# Get from: https://pc.testnet.0g.ai → Dashboard → API Keys
OG_COMPUTE_API_KEY=sk-
OG_COMPUTE_BASE_URL=https://router-api-testnet.integratenetwork.work/v1
OG_COMPUTE_MODEL=zai-org/GLM-5-FP8

# ─── 0G STORAGE ────────────────────────────────────────────────
OG_STORAGE_RPC=https://evmrpc-testnet.0g.ai
OG_STORAGE_INDEXER=https://indexer-storage-testnet-turbo.0g.ai
OG_STORAGE_PRIVATE_KEY=           # testnet wallet private key
STORAGE_SIDECAR_URL=http://storage-sidecar:3001

# ─── 0G CHAIN ──────────────────────────────────────────────────
OG_CHAIN_RPC=https://evmrpc-testnet.0g.ai
OG_CHAIN_ID=16602
DEPLOYER_PRIVATE_KEY=             # same as OG_STORAGE_PRIVATE_KEY for testnet
REGISTRY_CONTRACT_ADDRESS=        # filled after deploy

# ─── PAYCREST ──────────────────────────────────────────────────
# IMPORTANT: Use a SEPARATE Paycrest sender account from Sterling Concierge.
# Paycrest supports only ONE webhook URL per account.
# Ola needs its own API key, secret, and webhook URL.
# Apply at: https://app.paycrest.io → sign up as Sender → complete KYB
PAYCREST_API_KEY=                  # Ola-specific key (not Sterling's)
PAYCREST_WEBHOOK_SECRET=           # from Ola sender dashboard settings
PAYCREST_REFUND_ADDRESS=           # EVM wallet for crypto refunds on failed offramp
# Base URL — always v2
PAYCREST_BASE_URL=https://api.paycrest.io/v2

# ─── DATABASE ──────────────────────────────────────────────────
POSTGRES_DB=ola
POSTGRES_USER=ola
POSTGRES_PASSWORD=
DATABASE_URL=postgresql+asyncpg://ola:<pw>@db:5432/ola

# ─── APP ───────────────────────────────────────────────────────
SECRET_KEY=                        # openssl rand -hex 32
DEBUG=true

# ─── FRONTEND ──────────────────────────────────────────────────
BACKEND_URL=http://backend:8000    # internal docker network
NEXT_PUBLIC_APP_NAME=Ola
```

---

## 12. Python Dependencies

```
# backend/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
openai==1.40.0          # used for 0G Compute Router (OpenAI-compatible)
httpx==0.27.0
web3==7.0.0             # for 0G Chain OrderRegistry
sqlalchemy[asyncio]==2.0.31
asyncpg==0.29.0
alembic==1.13.2
pydantic-settings==2.4.0
python-dotenv==1.0.1
```

---

## 13. docker-compose.yml

```yaml
services:

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  storage-sidecar:
    build: ./storage-sidecar
    env_file: .env
    restart: unless-stopped

  backend:
    build: ./backend
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      storage-sidecar:
        condition: service_started
    restart: unless-stopped

  frontend:
    build: ./frontend
    env_file: .env
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## 14. One-Time Setup (Do This First)

### Step 1 — 0G Testnet Wallet
1. Create fresh MetaMask wallet (never reuse a real wallet for testnet)
2. Add 0G Testnet: RPC `https://evmrpc-testnet.0g.ai`, ChainID `16602`
3. Fund at https://faucet.0g.ai
4. Export private key → `DEPLOYER_PRIVATE_KEY` and `OG_STORAGE_PRIVATE_KEY`

### Step 2 — 0G Compute API Key
1. Go to https://pc.testnet.0g.ai
2. Connect wallet → Deposit testnet OG tokens
3. Dashboard → API Keys → Create → `inference` permission
4. Copy → `OG_COMPUTE_API_KEY`

### Step 3 — Deploy OrderRegistry
```bash
cd contracts
npm install
cp ../.env.example ../.env  # fill DEPLOYER_PRIVATE_KEY and OG_CHAIN_RPC
npx hardhat run scripts/deploy.ts --network og_testnet
# Copy output address → REGISTRY_CONTRACT_ADDRESS in .env
```

### Step 4 — Paycrest API Access
- Apply for Ola Sender API key: https://app.paycrest.io (separate account from Sterling — separate webhook URL)
- Paycrest is mainnet only. Test with $0.50 minimum orders.

---

## 15. Day-by-Day Build Plan

### Day 1 — June 17: Scaffold + Setup
- [ ] Create public GitHub repo: github.com/iamphantasm0/ola-sha with MIT license
- [ ] Full folder structure from Section 10
- [ ] `.env` from `.env.example`, fill 0G keys and Paycrest key
- [ ] Deploy `OlaRegistry.sol` to 0G testnet, save address
- [ ] `docker-compose up db storage-sidecar` — both healthy
- [ ] Verify: `curl POST storage-sidecar:3001/store` works, returns rootHash

### Day 2 — June 18: Provider + Agent Foundation
- [ ] `PaycrestProvider.get_offramp_quote()` — real API call, returns `QuoteResult`
- [ ] `PaycrestProvider.get_onramp_quote()` — same
- [ ] `agent/tools.py` — all 10 tool definitions complete
- [ ] `agent/prompts.py` — all state prompts written
- [ ] `agent/client.py` — 0G Compute Router wired
- [ ] Test: raw 0G Compute call with `get_offramp_quote` tool → model calls it correctly
- [ ] Test: raw 0G Compute call in `OFFRAMP_PROCESSING` state (no tools) → model responds without tool calls

### Day 3 — June 19: Backend Chat Endpoint + Order Flow
- [ ] DB models + Alembic migration (Session, Order, ConversationMessage)
- [ ] `repositories/` — all CRUD operations
- [ ] `POST /api/v1/chat` endpoint — full agent loop with dispatcher
- [ ] Test full offramp flow end-to-end via curl:
  - "sell 200 USDT" → quote returned
  - "yes" → state moves to COLLECTING_BANK
  - provide bank details → Paycrest order created, deposit address returned
- [ ] Test full onramp flow similarly

### Day 4 — June 20: Webhook + 0G Writes
- [ ] `POST /webhooks/paycrest` — signature verification
- [ ] On SETTLED: `store_transaction_record()` → get rootHash
- [ ] On SETTLED: `log_to_registry()` → 0G Chain write, get tx hash
- [ ] Update order in DB with both hashes
- [ ] Verify: rootHash visible on https://storagescan-galileo.0g.ai
- [ ] Verify: tx visible on https://chainscan-galileo.0g.ai

### Day 5 — June 21: Frontend
- [ ] Next.js 14 scaffold with Tailwind + shadcn/ui
- [ ] `ChatWindow.tsx` — message list, scrolls to bottom
- [ ] `MessageBubble.tsx` — user (right, dark) vs AI (left, lighter)
- [ ] `InputBar.tsx` — textarea + send on Enter
- [ ] `StatusPanel.tsx` — shows current state, amount, currency, Paycrest ref
- [ ] `ReceiptCard.tsx` — shows storage hash as link to StorageScan when settled
- [ ] `useChat.ts` hook — posts to `/api/chat`, updates messages, updates sidebar
- [ ] Session ID generation (UUID in localStorage)
- [ ] Full flow demoed in browser, both directions

### Day 6 — June 22: Polish + Demo + Submit
- [ ] Error states: 0G Compute timeout, Paycrest API error, invalid account number
- [ ] Loading states in UI (typing indicator while AI thinks)
- [ ] `README.md`: what Ola is, architecture diagram (ASCII), setup instructions,
  0G Storage Explorer link, 0G Chain Explorer link, demo video link
- [ ] Record demo video (2–3 min):
  1. Open web UI
  2. Offramp: "sell 200 USDT for NGN" → full flow → show settled with storage hash
  3. Click storage hash → show StorageScan with the record
  4. Show ChainScan with the registry tx
  5. Onramp: "buy 50 USDT" → full flow
- [ ] Push to public GitHub
- [ ] Submit at https://0g.ai/arena/login?next=/h/zero-cup before **June 23**

---

## 16. Key Links

| Resource | URL |
|---|---|
| Zero Cup (submit) | https://0g.ai/arena/login?next=/h/zero-cup |
| Competition Rules | https://0g.ai/arena/zero-cup/competition-rules |
| 0G Docs | https://docs.0g.ai |
| 0G Compute Quickstart | https://docs.0g.ai/developer-hub/building-on-0g/compute-network/router/quickstart |
| 0G Compute Models | https://docs.0g.ai/developer-hub/building-on-0g/compute-network/router/models |
| 0G Compute UI (testnet) | https://pc.testnet.0g.ai |
| 0G Storage SDK | https://docs.0g.ai/developer-hub/building-on-0g/storage/sdk |
| 0G Storage TS Starter Kit | https://github.com/0gfoundation/0g-storage-ts-starter-kit |
| 0G Chain Deploy Docs | https://docs.0g.ai/developer-hub/building-on-0g/contracts-on-0g/deploy-contracts |
| 0G Testnet Faucet | https://faucet.0g.ai |
| 0G Chain Explorer | https://chainscan-galileo.0g.ai |
| 0G Storage Explorer | https://storagescan-galileo.0g.ai |
| Paycrest Docs | https://docs.paycrest.io |
| Paycrest Sender API v2 | https://docs.paycrest.io/implementation-guides/sender-api-integration |
| Paycrest App (create account) | https://app.paycrest.io |
| Paycrest API Reference | https://docs.paycrest.io/api-reference/sender/initiate-payment-order-v2 |
| OpenZeppelin Contracts | https://github.com/OpenZeppelin/openzeppelin-contracts |

---

## 17. What Judges Will Verify

1. **0G Compute is doing real work** — every AI response goes through 0G Router. Check: repo shows `base_url=router-api.0g.ai` and system prompt shows Ola persona
2. **0G Storage has a real record** — paste the rootHash from the receipt into storagescan-galileo.0g.ai and it resolves
3. **0G Chain has a real tx** — paste the registry tx hash into chainscan-galileo.0g.ai and it resolves to `logSettlement()`
4. **Working demo** — judges open the URL, type "sell 100 USDT", and something happens
5. **Real use case** — African crypto offramp with live Paycrest integration is verifiable and undeniable

**Differentiation from 99% of entries:** Most submissions will be AI chatbots with 0G as a bolt-on decoration. This submission has a transaction that flows from user intent → AI tool call → Paycrest settlement → 0G Storage → 0G Chain in one end-to-end flow. All three 0G services are essential and verifiable.

---

## 18. License

Add a `LICENSE` file to the repo root with the following content.

**BSL 1.1 — Business Source License**
Readable by judges. Non-commercial by default. Converts to MIT after 4 years.
Vela Labs retains commercial rights until then.

```
Business Source License 1.1

Licensor:             Vela Labs (Chibuzor Adigwe)
Licensed Work:        Ola — AI-Powered Crypto ↔ Fiat Exchange
                      Copyright (c) 2026 Vela Labs
Change Date:          2030-06-17
Change License:       MIT

Additional Use Grant: You may use the Licensed Work for non-production,
                      evaluation, and personal purposes only. Any use of
                      the Licensed Work in a production environment or for
                      commercial purposes requires a separate written
                      agreement with Vela Labs.

Contact:              hello@velalabs.io

---

On the Change Date (2030-06-17), the Licensed Work will automatically
be made available under the MIT License:

  Permission is hereby granted, free of charge, to any person obtaining
  a copy of this software and associated documentation files (the
  "Software"), to deal in the Software without restriction, including
  without limitation the rights to use, copy, modify, merge, publish,
  distribute, sublicense, and/or sell copies of the Software, and to
  permit persons to whom the Software is furnished to do so, subject to
  the following conditions:

  The above copyright notice and this permission notice shall be
  included in all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
  NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
  BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
  ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.

---

For the full BSL 1.1 text, see:
https://mariadb.com/bsl11/
```

### What this means in practice

| Who | Can they use it? |
|---|---|
| Zero Cup judges | ✅ Read, run, verify |
| Developers evaluating | ✅ Clone, test locally |
| Someone wanting to compete | ❌ Cannot ship commercially without Vela Labs permission |
| After June 17, 2030 | ✅ Full MIT — anyone, anything |

Add this to `README.md` badge row:
```markdown
[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-blue.svg)](LICENSE)
Built by [Vela Labs](https://velalabs.io) · Powered by [0G](https://0g.ai)
```
