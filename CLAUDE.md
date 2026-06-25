# Ola — context for AI coding assistants

Ola is an AI-driven crypto ↔ fiat exchange. A chat UI talks to a 0G Compute LLM
that calls tools to drive onramp/offramp flows; Paycrest moves the money; 0G
Storage + 0G Chain provide a verifiable audit trail.

## Layout
- `backend/`          FastAPI agent loop, Paycrest provider, webhook, 0G clients
- `storage-sidecar/`  Node service wrapping the 0G Storage TS SDK
- `contracts/`        Hardhat + `OlaRegistry.sol` (0G Chain settlement log)
- `frontend/`         Next.js 14 chat UI + transaction sidebar

## Confirmed facts (do not re-guess)
- Paycrest Sender API **v2**: one endpoint `POST /v2/sender/orders` for both
  ramps; amounts are **strings**; never pass `rate` on create; institution
  **codes** not bank names; webhook events lowercase; HMAC-SHA256 hex compare.
- 0G Compute Router is **OpenAI-compatible**. Model `zai-org/GLM-5-FP8`.
- 0G Storage SDK: `@0gfoundation/0g-ts-sdk` + **ethers v6**.
- 0G Chain testnet (Galileo): RPC `https://evmrpc-testnet.0g.ai`, chainId **16602**.

## Architectural invariants
- Tools are state-gated by `TOOLS_BY_STATE`; the dispatcher re-checks the gate
  server-side. Never let a tool run out of state.
- Paycrest order creation happens ONLY in `submit_bank_details` /
  `submit_wallet_address`.
- 0G Storage + 0G Chain writes happen ONLY in the Paycrest `settled` webhook.

## Section A note
`.0g-skills/` and the `0g-cc` MCP server are for a LOCAL Claude Code session and
are gitignored — they are not part of the deployed app.

For all network endpoints / chain IDs / SDK examples, see https://docs.0g.ai/ai-context
