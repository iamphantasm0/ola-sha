# Ola — AI-Powered Crypto ↔ Fiat Exchange

[![License: BSL 1.1](https://img.shields.io/badge/License-BSL_1.1-blue.svg)](LICENSE)

Chat with an AI to swap **stablecoins ↔ local currency** in both directions —
onramp (fiat → crypto) and offramp (crypto → fiat) — across six corridors:
**NGN · KES · UGX · TZS · MWK · BRL**.

> _A Sterling Concierge demo by [Vela Labs](https://velalabs.io). Built for Zero Cup 2026._

The AI runs on **0G Compute** and calls tools to drive the flow. **Paycrest**
moves the money. Every settled order writes an immutable audit record to **0G
Storage** and an append-only settlement row to **0G Chain** — so any third
party can verify a transaction end to end.

All three 0G services do real, essential work:

| Service | Role | Verify it |
| --- | --- | --- |
| **0G Compute** | Drives the whole conversation (OpenAI-compatible router, `zai-org/GLM-5-FP8`) | Every reply is a router call |
| **0G Storage** | Immutable audit record per settled order → `rootHash` | Paste the hash into [StorageScan](https://storagescan-galileo.0g.ai) |
| **0G Chain** | Append-only `logSettlement()` on `OlaRegistry` → tx hash | Paste the tx into [ChainScan](https://chainscan-galileo.0g.ai) |

---

## Architecture

```
              Next.js 14 chat UI  ──POST /api/v1/chat──▶  FastAPI backend
              (chat + tx sidebar)                          │
                                                           ├─ Agent loop (0G Compute, state-gated tools)
                                                           ├─ Paycrest provider  (real money, both ramps)
                                                           ├─ 0G Storage client ─▶ Node sidecar (0G TS SDK)
                                                           └─ 0G Chain client   ─▶ OlaRegistry (web3.py)
                                                           │
                                          PostgreSQL  ◀────┘  (orders · sessions · messages)

        Paycrest webhook ──▶ /api/v1/webhooks/paycrest ──▶ on `settled`: write 0G Storage + 0G Chain
```

### Why it’s hard to fake
A transaction flows from **user intent → AI tool call → Paycrest settlement →
0G Storage → 0G Chain** in one end-to-end path. The AI can only call the tools
valid for the current order state (`TOOLS_BY_STATE`), and the dispatcher
re-checks that gate server-side — a hallucinated tool call can never execute
out of state.

---

## Repo layout

```
backend/         FastAPI agent loop, Paycrest provider, webhook, 0G clients
storage-sidecar/ Node + @0gfoundation/0g-ts-sdk (ethers v6) — store/fetch records
contracts/       Hardhat + OlaRegistry.sol (0G Chain settlement log) + tests
frontend/        Next.js 14 chat UI + transaction sidebar
docker-compose.yml
```

---

## Quick start

### 0. Prerequisites
- Docker + Docker Compose
- A funded **0G testnet** wallet (faucet: https://faucet.0g.ai — 0.1 OG/day)
- A **0G Compute** API key (https://pc.testnet.0g.ai → Dashboard → API Keys)
- A **Paycrest sender** account — **separate from Sterling Concierge**
  (one webhook URL per account). Apply at https://app.paycrest.io

### 1. Configure
```bash
cp .env.example .env
# Fill: OG_COMPUTE_API_KEY, OG_STORAGE_PRIVATE_KEY, DEPLOYER_PRIVATE_KEY,
#       PAYCREST_API_KEY, PAYCREST_WEBHOOK_SECRET, PAYCREST_REFUND_ADDRESS
```

### 2. Deploy the OlaRegistry contract (0G testnet)
```bash
cd contracts
npm install
npm run deploy:testnet
# Copy the printed address into REGISTRY_CONTRACT_ADDRESS in ../.env
```

### 3. Run everything
```bash
docker compose up --build
# frontend  → http://localhost:3000
# backend   → http://localhost:8000  (health: /health)
```
In `DEBUG=true` the backend creates tables on startup. For production run
`alembic upgrade head` (see `backend/alembic`) and set `DEBUG=false`.

### 4. Point the Paycrest webhook at the backend
Set your Ola sender account's webhook URL to:
```
https://<your-public-host>/api/v1/webhooks/paycrest
```
For local testing, tunnel port 8000 (e.g. with a reverse tunnel) so Paycrest can reach it.

---

## What judges can verify

1. **0G Compute is doing real work** — every AI reply is a router call;
   `OG_COMPUTE_BASE_URL` points at the 0G router and the system prompt is the
   Ola persona.
2. **0G Storage has a real record** — the receipt’s `rootHash` resolves on
   https://storagescan-galileo.0g.ai.
3. **0G Chain has a real tx** — the registry tx hash resolves to
   `logSettlement()` on https://chainscan-galileo.0g.ai.
4. **Working demo** — open the URL, type _“sell 100 USDT for NGN”_, and the
   full flow runs with live Paycrest settlement.

> **Paycrest note:** Paycrest settles on mainnet; test orders have a **$0.50
> minimum**. Settlement is typically under 30s for NGN but is never promised as
> “instant.”

---

## Notes for builders
- The contracts, provider, dispatcher, and webhook are the differentiated core;
  the frontend is intentionally lean (Tailwind, no component-library setup).
- The 0G Storage sidecar follows the official
  [starter kit](https://github.com/0gfoundation/0g-storage-ts-starter-kit)
  upload/download pattern. If your installed SDK version exposes slightly
  different symbols, adjust `storage-sidecar/src/lib/zg.ts` — the package name
  (`@0gfoundation/0g-ts-sdk`) is the confirmed one.
- `.0g-skills/` and the `0g-cc` MCP server (scope Section A) configure a local
  Claude Code session; they are gitignored and not part of the deployed app.

---

Built by [Vela Labs](https://velalabs.io) · Powered by [0G](https://0g.ai)
