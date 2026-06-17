"""Phase 2 smoke test — RUN THIS FIRST on Day 2.

Verifies the 0G Compute Router model:
  1. emits a well-formed tool call when given a tool and a matching request
  2. emits NO tool call when given an empty tool list (the *_PROCESSING states)
  3. does not leak <think> reasoning into message.content (thinking-model check)

Usage:
    cd backend && python scripts/smoke_compute.py
Requires OG_COMPUTE_API_KEY / OG_COMPUTE_BASE_URL / OG_COMPUTE_MODEL in repo-root .env.
"""

import asyncio
import json
import sys

sys.path.insert(0, ".")

from app.agent.client import og_client  # noqa: E402
from app.agent.tools import ALL_TOOLS  # noqa: E402
from app.core.config import settings  # noqa: E402

OFFRAMP_TOOL = [ALL_TOOLS["get_offramp_quote"]]


async def test_emits_tool_call() -> bool:
    resp = await og_client.chat.completions.create(
        model=settings.OG_COMPUTE_MODEL,
        messages=[
            {"role": "system", "content": "You are Ola. Use tools when the user wants to trade."},
            {"role": "user", "content": "I want to sell 200 USDT for Nigerian naira"},
        ],
        tools=OFFRAMP_TOOL,
        tool_choice="auto",
        max_tokens=500,
        temperature=0.2,
    )
    choice = resp.choices[0]
    tool_calls = choice.message.tool_calls
    if not tool_calls:
        print("  ✗ no tool call emitted. content=", (choice.message.content or "")[:200])
        return False
    tc = tool_calls[0]
    try:
        args = json.loads(tc.function.arguments)
    except Exception as e:  # noqa: BLE001
        print("  ✗ tool arguments not valid JSON:", tc.function.arguments, e)
        return False
    print(f"  ✓ tool={tc.function.name} args={args}")
    return tc.function.name == "get_offramp_quote" and args.get("token") == "USDT"


async def test_no_tool_call_when_empty() -> bool:
    resp = await og_client.chat.completions.create(
        model=settings.OG_COMPUTE_MODEL,
        messages=[
            {"role": "system", "content": "Settlement in progress. Tell the user to wait."},
            {"role": "user", "content": "is it done yet?"},
        ],
        tools=None,
        max_tokens=200,
        temperature=0.2,
    )
    choice = resp.choices[0]
    content = choice.message.content or ""
    has_tool = bool(choice.message.tool_calls)
    leaked = "<think>" in content.lower()
    print(f"  {'✓' if not has_tool else '✗'} no tool call (got tool_calls={has_tool})")
    print(f"  {'✓' if not leaked else '✗'} no <think> leak. reply={content[:150]!r}")
    return (not has_tool) and (not leaked)


async def main():
    print(f"Model: {settings.OG_COMPUTE_MODEL}")
    print(f"Base:  {settings.OG_COMPUTE_BASE_URL}\n")

    print("[1] emits well-formed tool call:")
    t1 = await test_emits_tool_call()
    print("\n[2] no tool call when tools empty + no reasoning leak:")
    t2 = await test_no_tool_call_when_empty()

    print("\n=== RESULT ===")
    if t1 and t2:
        print("PASS — model is safe for the state-gated agent.")
    else:
        print("FAIL — review above. Try fallback model 0GM-1.0-35B-A3B or adjust thinking mode.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
