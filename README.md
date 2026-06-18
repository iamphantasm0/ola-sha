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

## License
Business Source License 1.1 — see [LICENSE](LICENSE). Converts to MIT on 2030-06-17.
