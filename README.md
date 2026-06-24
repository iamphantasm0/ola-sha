# Ola — AI-Powered Crypto ↔ Fiat Exchange

[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-blue.svg)](LICENSE)
Built by Vela Labs · Powered by [0G](https://0g.ai)

Ola is a web-based AI chat interface that lets users in Africa and LATAM swap between
stablecoins (USDC/USDT) and local currency (NGN, KES, UGX, TZS, MWK, BRL) in both
directions — onramp (fiat → crypto) and offramp (crypto → fiat).

The AI runs on **0G Compute**, drives the whole conversation, and calls tools to execute
the flow. **Paycrest** moves the money. **0G Storage** writes an immutable audit record per
settled transaction. **0G Chain** holds a lightweight on-chain settlement log (`OlaRegistry`).

## All three 0G services do real, verifiable work

1. **Compute** — every AI turn goes through the 0G Compute Router (OpenAI-compatible).
2. **Storage** — at settlement, the audit record is written to 0G Storage; the root hash
   resolves on [storagescan-galileo.0g.ai](https://storagescan-galileo.0g.ai).
3. **Chain** — the settlement is logged to `OlaRegistry` on 0G testnet (Galileo); the tx
   resolves on [chainscan-galileo.0g.ai](https://chainscan-galileo.0g.ai).

## How to use

**Live app: https://ola-sha.up.railway.app**

Ola is a chat. Just tell it what you want in plain language — it figures out the rest, and
every money decision is a one-tap button (the AI never handles your funds directly).

### Sell stablecoins for cash (offramp)
1. Type something like **"sell 200 USDC for naira"**. Ola replies with a live quote.
2. Choose where to receive the cash: a **saved bank** (one tap) or **"Use a different account"**
   (enter bank name + account number — Ola verifies the account holder name for you).
3. Confirm. Ola gives you a **deposit address**; send the stablecoin to it from any wallet.
4. Ola tracks it. On settlement you get a **receipt** with a verifiable 0G record.

### Buy stablecoins with cash (onramp)
1. Type **"buy 50 USDC with naira"** → live quote.
2. Give the **wallet address** to receive the crypto (and network — Base or Arbitrum). No bank
   needed to buy.
3. Ola shows a **bank account + exact amount** to transfer. Pay it.
4. The stablecoin lands in your wallet, and you get the same 0G receipt.

### Optional: sign in
Create an account (email + password) to **save your bank and wallet** — next time they're a single
tap. You can transact without an account too.

### Verify any settlement on 0G (no wallet or login needed)
There's a public **[Verify page](https://ola-sha.up.railway.app/verify)** — pick any settlement and
hit **"Verify live"**: it re-fetches the audit record from **0G Storage** and confirms the settlement
tx on **0G Chain**, in real time, against the network itself.

The receipt also shows two **public explorer** links:
- **0G Storage record** → the immutable audit record's Merkle root on 0G Storage.
- **0G Chain settlement** → the on-chain `logSettlement` tx on the `OlaRegistry` contract. Open its
  **Logs** tab and you'll find the storage hash embedded in the `OrderSettled` event — so one chain
  link proves both 0G layers.

**Supported:** corridors NGN · KES · UGX · TZS · MWK · BRL · tokens USDC / USDT · $1–$4,999 per
transaction · settlement typically under 30s for NGN.

## Architecture

```
Next.js 14 chat UI  ──POST /api/chat──►  FastAPI backend
   (split-pane,                              │
    polls /api/order/:id)                    ├─ Agent: state-gated tool firewall → 0G Compute Router
                                             ├─ PaycrestProvider (Sender API v2, onramp + offramp)
                                             ├─ PostgreSQL (orders, sessions, conversation history)
                                             ▼
                            Paycrest webhook ──► verify → flip state → 200
                                             └─(BackgroundTask)─► 0G Storage sidecar (rootHash)
                                                                  → OlaRegistry on 0G Chain (tx)
```

The agent injects **only the tools valid for the current order state** (`TOOLS_BY_STATE`),
and the dispatcher re-checks the same gate before executing — a double-gated firewall.

## Repository layout

| Path | What |
|---|---|
| `backend/` | FastAPI: agent loop, dispatcher firewall, Paycrest provider, 0G services |
| `backend/scripts/smoke_compute.py` | **Run first** — verifies model tool-calling on 0G Compute |
| `storage-sidecar/` | Node/Express wrapper around `@0glabs/0g-ts-sdk` (Storage) |
| `contracts/` | `OlaRegistry.sol` + Hardhat (deploy to 0G testnet) |
| `frontend/` | Next.js 14 chat UI + status sidebar |

## Setup

### 0. Prerequisites
- Docker + Docker Compose, Node 20+, Python 3.12+
- A funded 0G testnet wallet, a 0G Compute API key, and a Paycrest sender account
- `cp .env.example .env` and fill every value

### 1. Deploy the registry contract
```bash
cd contracts
npm install
npm test                      # 3 tests pass (compiled with evmVersion: cancun)
npm run deploy:testnet        # prints address → set REGISTRY_CONTRACT_ADDRESS in .env
```

### 2. Verify 0G Compute tool-calling (do this before building on it)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/smoke_compute.py   # must PASS before the agent is trustworthy
```

### 3. Run everything
```bash
docker compose up --build
# frontend  → http://localhost:3000
# backend   → http://localhost:8000/health
# sidecar   → internal only (no host port); reachable as http://storage-sidecar:3001
#             from the backend. To probe it: docker compose exec backend \
#             curl -s -H "x-sidecar-token: $SIDECAR_AUTH_TOKEN" storage-sidecar:3001/health
```

> **Security:** the sidecar is not published to the host and requires `SIDECAR_AUTH_TOKEN`
> on every request; the order status endpoint is scoped to the owning session id.

### 4. Settlement detection — webhook OR polling
Settlement (the trigger for the 0G writes) is detected two ways, both funneling through
the same logic in `app/services/settlement.py`:

- **Polling (default, no setup):** a background reconciler polls each active order's status
  via `GET /sender/orders/:id` every `RECONCILE_INTERVAL` seconds (default 10) and runs the
  settlement logic. Asking "is it done?" in chat also reconciles on demand. **This works
  with a single shared Paycrest account** — no dedicated webhook URL needed.
- **Webhook (optional, lower latency):** if/when Ola has its **own** Paycrest sender account,
  point its webhook at `https://<your-host>/api/v1/webhooks/paycrest` (ngrok for local). The
  webhook and poller are idempotent and safe to run together.

## Demo flow (offramp)
1. "sell 200 USDT for NGN" → AI returns a quote (0G Compute + Paycrest rates)
2. "yes" → AI collects bank details → Paycrest order created → deposit address shown
3. Send USDT to the deposit address
4. On Paycrest `settled`: audit record → 0G Storage, settlement → 0G Chain
5. Sidebar shows the storage hash (→ StorageScan) and registry tx (→ ChainScan)

## Network config (0G testnet — Galileo)
| | |
|---|---|
| Chain RPC | `https://evmrpc-testnet.0g.ai` |
| Chain ID | `16602` |
| Storage indexer | `https://indexer-storage-testnet-turbo.0g.ai` |
| Chain explorer | `https://chainscan-galileo.0g.ai` |
| Storage explorer | `https://storagescan-galileo.0g.ai` |

## Notes
- **Storage SDK:** `@0gfoundation/0g-storage-ts-sdk` (the current package, v1.2.x — the old
  `@0glabs/0g-ts-sdk@0.3.3` produces a submission format the current testnet flow contract
  rejects with `require(false)`). ethers **v6**, `evmVersion: cancun`.
- **0G Compute model:** default **MiniMax-M3** (free, native tool use, verifiable, 1M ctx);
  fallback **0GM-1.0-35B-A3B**. Confirm exact model-id strings from the router `/models`.
- **Paycrest** is mainnet-only with a $0.50 minimum — the live demo moves small real funds.
- MVP creates DB tables on startup; swap for Alembic migrations before production.

## Roadmap

Ola is a Zero Cup 2026 entry (a 6-round knockout: Group Stage → Round of 32 → 16 → QF → SF → Final).
Plan by round:
.

**Bigger bets (later rounds / if it gets competitive):**
- **`/mywallet` — managed wallets per user** (like Sterling Concierge): Ola custodies/manages a
  wallet for each user so they can buy/sell without bringing their own. Needs wallet infra + secure
  key management (e.g. an embedded-wallet provider or MPC).
- **Telegram bot** — the same state-gated agent over Telegram for reach beyond the web app.

## License
Business Source License 1.1 — see [LICENSE](LICENSE). Converts to MIT on 2030-06-17.
