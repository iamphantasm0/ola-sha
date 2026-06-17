"""End-to-end agent-logic test with NO live credentials.

Mocks ONLY the two external edges — the 0G Compute client and the Paycrest provider —
and drives the REAL chat endpoint, dispatcher firewall, state machine, and Postgres DB
through a full offramp conversation. Proves:
  - quote -> QUOTING -> confirm -> COLLECTING_BANK -> submit -> AWAITING_DEPOSIT transitions
  - bank name -> institution code resolution path
  - Paycrest order creation only at submit_bank_details
  - the state firewall BLOCKS a tool the model tries to call out of turn

Run:  (postgres on :55432)  python scripts/test_agent_flow.py
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, ".")

# Point at the throwaway test DB + dummy secrets BEFORE importing app modules.
os.environ["DATABASE_URL"] = "postgresql+asyncpg://ola:test@localhost:55432/ola_test"
os.environ["OG_COMPUTE_API_KEY"] = "test"
os.environ["PAYCREST_API_KEY"] = "test"
os.environ["DEBUG"] = "false"  # quiet SQL echo

import app.api.v1.chat as chat_mod  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.core.db import engine  # noqa: E402
from app.models import Base  # noqa: E402
from app.providers.base import OrderResult, PaymentInstructions, QuoteResult  # noqa: E402

from httpx import ASGITransport, AsyncClient  # noqa: E402

SESSION = "11111111-1111-1111-1111-111111111111"

PASS, FAIL = "\033[92mPASS\033[0m", "\033[91mFAIL\033[0m"
results: list[bool] = []


def check(label: str, cond: bool):
    results.append(cond)
    print(f"  [{PASS if cond else FAIL}] {label}")


# ─── Fake 0G Compute client ───────────────────────────────────────────────────


class _Fn:
    def __init__(self, name, args):
        self.name = name
        self.arguments = json.dumps(args)


class _ToolCall:
    def __init__(self, name, args):
        self.id = f"call_{name}"
        self.function = _Fn(name, args)


class _Msg:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self):
        return {"role": "assistant", "content": self.content or ""}


class _Choice:
    def __init__(self, msg):
        self.message = msg
        self.finish_reason = "tool_calls" if msg.tool_calls else "stop"


class _Resp:
    def __init__(self, msg):
        self.choices = [_Choice(msg)]


class FakeCompletions:
    """Pops scripted responses in order. Each create() call consumes one."""

    def __init__(self):
        self.queue: list[_Msg] = []

    async def create(self, *args, **kwargs):
        assert self.queue, "FakeCompletions queue empty — script more responses"
        return _Resp(self.queue.pop(0))


class FakeChat:
    def __init__(self, comp):
        self.completions = comp


class FakeOG:
    def __init__(self):
        self.completions = FakeCompletions()
        self.chat = FakeChat(self.completions)


# ─── Fake Paycrest provider ───────────────────────────────────────────────────


class FakePaycrest:
    async def get_offramp_quote(self, token, amount, currency):
        return QuoteResult(
            provider="fake", direction="offramp", input_amount=amount, input_currency=token,
            output_amount=amount * 1580.0, output_currency=currency, rate=1580.0,
            fee=0.5, fee_currency=token,
        )

    async def resolve_institution_code(self, currency, bank_name):
        return "GTBINGLA" if "gt" in bank_name.lower() else None

    async def verify_bank_account(self, code, account_number):
        return "JOHN DOE"

    def __init__(self):
        self.next_status = "initiated"

    async def create_offramp_order(self, **kwargs):
        return OrderResult(
            provider="fake", provider_order_id="PCRST-TEST-001", status="initiated",
            payment_instructions=PaymentInstructions(
                direction="offramp",
                deposit_address="0xDEADBEEF00000000000000000000000000000001",
                deposit_token=kwargs["token"], deposit_network="base",
                valid_until="2026-06-17T23:59:59Z",
            ),
            raw={},
        )

    async def get_order_status(self, provider_order_id):
        # The poller / check_* tools read this. Tests flip self.next_status.
        return {"id": provider_order_id, "status": self.next_status,
                "direction": "offramp", "txHash": "0xPAYCRESTTX", "updatedAt": "2026-06-17T21:00:00Z"}


async def turn(client, message):
    r = await client.post("/api/v1/chat", json={"session_id": SESSION, "message": message})
    return r.json()


async def main():
    # Real tables on the test DB.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    fake_og = FakeOG()
    fake_provider = FakePaycrest()
    chat_mod.og_client = fake_og
    chat_mod.provider = fake_provider

    # Mock the 0G writes so settlement runs without a sidecar or chain RPC.
    import app.services.settlement as settle_mod

    async def fake_store(record):
        return "0xROOTHASH_FROM_0G_STORAGE"

    async def fake_chain(**kwargs):
        return "0xCHAINTX_FROM_0G_REGISTRY"

    settle_mod.store_transaction_record = fake_store
    settle_mod.log_to_registry = fake_chain

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1: quote
        fake_og.completions.queue = [
            _Msg(tool_calls=[_ToolCall("get_offramp_quote", {"token": "USDT", "amount": 200, "currency": "NGN"})]),
            _Msg(content="You'll receive ₦316,000.00 for 200 USDT. Confirm?"),
        ]
        print("\nTurn 1 — 'sell 200 USDT for NGN'")
        r1 = await turn(client, "sell 200 USDT for NGN")
        check("state -> OFFRAMP_QUOTING", r1["order_state"]["status"] == "OFFRAMP_QUOTING")
        check("tool_called == get_offramp_quote", r1["tool_called"] == "get_offramp_quote")
        check("output_amount computed (316000)", r1["order_state"]["output_amount"] == 316000.0)

        # Turn 2: confirm
        fake_og.completions.queue = [
            _Msg(tool_calls=[_ToolCall("confirm_offramp", {})]),
            _Msg(content="Great — what's your bank name, account number, and account name?"),
        ]
        print("Turn 2 — 'yes'")
        r2 = await turn(client, "yes")
        check("state -> OFFRAMP_COLLECTING_BANK", r2["order_state"]["status"] == "OFFRAMP_COLLECTING_BANK")

        # Turn 3: submit bank details -> Paycrest order created
        fake_og.completions.queue = [
            _Msg(tool_calls=[_ToolCall("submit_bank_details", {
                "bank_name": "GTBank", "account_number": "0123456789", "account_name": "John Doe"})]),
            _Msg(content="Send exactly 200 USDT to 0xDEAD…0001 on Base."),
        ]
        print("Turn 3 — bank details")
        r3 = await turn(client, "GTBank, 0123456789, John Doe")
        check("state -> OFFRAMP_AWAITING_DEPOSIT", r3["order_state"]["status"] == "OFFRAMP_AWAITING_DEPOSIT")
        check("paycrest_order_id captured", r3["order_state"]["paycrest_order_id"] == "PCRST-TEST-001")
        check("deposit_address surfaced", r3["order_state"]["deposit_address"].startswith("0xDEADBEEF"))

        # Turn 4: FIREWALL — model goes rogue and calls a tool not allowed in this state.
        fake_og.completions.queue = [
            _Msg(tool_calls=[_ToolCall("get_offramp_quote", {"token": "USDT", "amount": 999, "currency": "NGN"})]),
            _Msg(content="(model attempted an out-of-state tool)"),
        ]
        print("Turn 4 — firewall (rogue get_offramp_quote in AWAITING_DEPOSIT)")
        r4 = await turn(client, "actually quote me 999 instead")
        check("state UNCHANGED (still AWAITING_DEPOSIT)", r4["order_state"]["status"] == "OFFRAMP_AWAITING_DEPOSIT")
        check("no new order created (blocked)", r4["order_state"]["paycrest_order_id"] == "PCRST-TEST-001")

        # Turn 5: user asks for status; Paycrest now reports settled -> reconcile drives 0G writes.
        fake_provider.next_status = "settled"
        fake_og.completions.queue = [
            _Msg(tool_calls=[_ToolCall("check_deposit_status", {})]),
            _Msg(content="Done! Your ₦316,000 is on the way. Receipt stored on 0G."),
        ]
        print("Turn 5 — 'is it done?' (Paycrest now settled, no webhook)")
        r5 = await turn(client, "is it done?")
        check("state -> SETTLED (via polling, no webhook)", r5["order_state"]["status"] == "SETTLED")
        check("0G Storage hash written", r5["order_state"]["storage_hash"] == "0xROOTHASH_FROM_0G_STORAGE")
        check("0G Chain tx written", r5["order_state"]["registry_tx_hash"] == "0xCHAINTX_FROM_0G_REGISTRY")

    print("\n=== RESULT ===")
    if all(results):
        print(f"{PASS} — agent loop, dispatcher firewall, and state machine all correct ({len(results)} checks).")
    else:
        print(f"{FAIL} — {results.count(False)}/{len(results)} checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
