# Changelog

All notable changes to Ola for Zero Cup 2026 submissions. Group Stage was submitted **2026-06-19**
from `main` / early deploy. Round of 32 ships from branch **`feat/cognee-memory`** unless noted.

---

## Round of 32 — submission window closes 2026-06-28

Ola is a stablecoin concierge: chat-driven onramp/offramp with **verifiable settlement on all three
0G services** (Compute, Storage, Chain). This round deepens proof, polish, and logged-in stickiness
— so judges can *touch* the 0G story without running a full ramp themselves.

### Added

- **Verify search & shareable links** — `/verify` accepts order UUID, storage hash, chain tx, or
  Paycrest ref (`GET /verify/lookup?q=`). Permalinks: `/verify?id=…`. Receipt sidebar deep-links to
  verify. Paginated recent list with **Load more**.
- **On-chain stats dashboard** — `GET /api/v1/stats/registry` reads live `totalSettlements()` and
  aggregates `OrderSettled` events (volume, corridors, onramp/offramp split). Shown on home sidebar
  and `/verify` (`OgRegistryStats`).
- **Inline 0G proof in chat** — at settlement, a **Notarized on 0G** card appears in the thread
  (storage + chain explorer links + verify deep link). No need to open the sidebar to see proof.
- **Downloadable PDF receipt** — **Download PDF** on settled Statement receipts and chat proof
  cards. Shareable document with amounts, 0G hashes, verified seal, and verify URL
  (`ola-receipt-{id}.pdf`).
- **Signed-in ramp history** — **Statement | History** sidebar tabs (desktop) and **History** on
  mobile. `GET /api/v1/orders/history` lists past ramps with status, **Download PDF**, and
  **Verify →** per entry.
- **Cognee memory layer** (parallel WeMakeDevs × Cognee track, `memory-sidecar/`) — per-user
  `remember` on settle, `recall` into chat (IDLE), `forget` via `/privacy/forget-me`. GPT-free:
  minimax-m3 on 0G + BAML + local fastembed. *Wired in repo; Railway deploy + demo pending Jun 29
  window.*

### Improved

- **Onramp wallet flow** — **Add a wallet** when none saved; **Use a different wallet** when saved
  wallets exist. Wallet picker shown in both quote and post-confirm states. Wallets auto-save on
  submit when logged in; optional **Save this wallet** on the payment step (parity with saved banks).
- **AI depth** (carried from pre–Round of 32) — `get_market_insights`, `get_help`, markdown in chat
  bubbles, deterministic presenter for all money fields.

### Fixed

- **Local verify lookup** — Next.js backend proxy now forwards query strings (`?q=`, `?cursor=`).
  Hash normalization accepts missing `0x` and common `8x` typo.
- **History API 500** — `/orders/history` route must register before `/orders/{order_id}`; invalid
  UUIDs in `get_by_id` no longer crash the server. Clearer auth error copy in the History panel.

### For judges — quick demo path

1. Open [ola-sha.up.railway.app](https://ola-sha.up.railway.app) *(deploy `feat/cognee-memory` for
   latest)* or run locally via `docker compose up`.
2. **Verify without login** — `/verify` → search a hash or pick recent → **Verify live** (Storage +
   Chain re-check).
3. **Full ramp** — sign in → buy/sell → settle → see inline 0G proof → **Download PDF** → **History**
   tab for past ramps.
4. **On-chain** — sidebar stats + ChainScan / StorageScan links; `OrderSettled` embeds the storage
   hash.

### Contract & network

| | |
|---|---|
| Registry (Galileo testnet) | `0x8A2FC1327e4F03bc63857724FD1Afe44B54A0350` |
| Chain explorer | [chainscan-galileo.0g.ai](https://chainscan-galileo.0g.ai) |
| Storage explorer | [storagescan-galileo.0g.ai](https://storagescan-galileo.0g.ai) |

### Still planned (post–Round of 32)

- Agent tool-call trace (structured “what Ola did” log — not raw CoT)
- Demo video (2–3 min, script in Obsidian `demo-script.md`)
- Cognee live demo on Railway (second conversation + isolation proof)
- Telegram bot, reputation score from registry events

---

## Group Stage — submitted 2026-06-19

- Live deployed app on Railway with real Paycrest settlement
- End-to-end offramp/onramp state machine with deterministic money UI (buttons, not chat guesses)
- **0G Compute** (minimax-m3, tool-calling), **0G Storage** (audit record), **0G Chain**
  (`OlaRegistry` settlement log with embedded storage hash)
- Public **Verify** page — live re-fetch from Storage + Chain receipt check
- Email/password auth, saved bank accounts, session-scoped anonymous mode