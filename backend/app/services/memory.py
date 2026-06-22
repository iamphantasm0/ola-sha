"""
Memory service — thin HTTP client to the memory-sidecar (Cognee), for Ola's per-user memory
across sessions (WeMakeDevs × Cognee hackathon).

Cognee + its heavy/newer deps live in a SEPARATE service (memory-sidecar) so they never touch
the backend's dependency set (mirrors the storage-sidecar). This module just calls it over the
internal network. The validated, GPT-free config (minimax-m3 on 0G + BAML + local fastembed)
lives in memory-sidecar/app/main.py.

ARCHITECTURE BOUNDARY (do not violate): memory NEVER touches the state-gated tool firewall. It
only feeds read-only context into the system prompt. Every call degrades gracefully — if the
sidecar is unreachable or slow, recall returns "" and writes no-op, so the chat flow is unaffected.
"""
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE = settings.MEMORY_SIDECAR_URL.rstrip("/")
_HEADERS = {"x-sidecar-token": settings.SIDECAR_AUTH_TOKEN}


# --- dataset keys: stable per identity. Logged-in users get durable cross-session memory;
#     guests get session-scoped memory (session_id resets on a new chat). ---
def dataset_for_user(user, session_id: str) -> str:
    if user is not None and getattr(user, "id", None):
        return f"ola-user-{user.id}"
    return f"ola-anon-{session_id}"


def dataset_for_order(order) -> str:
    if getattr(order, "user_id", None):
        return f"ola-user-{order.user_id}"
    return f"ola-anon-{order.session_id}"


async def _post(path: str, payload: dict, timeout: float) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{_BASE}{path}", json=payload, headers=_HEADERS)
        resp.raise_for_status()
        return resp.json()


async def remember_fact(dataset: str, fact: str) -> None:
    """Store a structured fact. PII must already be masked by the caller. Never raises."""
    try:
        await _post("/remember", {"dataset": dataset, "fact": fact}, timeout=60.0)
    except Exception as e:  # noqa: BLE001 — memory must never break the core flow
        logger.warning("memory.remember failed (ignored): %s", e)


async def recall_context(dataset: str, query: str, limit: int = 5) -> str:
    """Pull relevant memory for the current turn, formatted for the system prompt. Returns "" for
    a new/anonymous user or if the sidecar is slow/unavailable — a safe, chat-unchanged default."""
    try:
        data = await _post("/recall", {"dataset": dataset, "query": query, "limit": limit}, timeout=30.0)
        return data.get("context", "")
    except Exception as e:  # noqa: BLE001
        logger.warning("memory.recall failed (ignored): %s", e)
        return ""


async def improve_memory(dataset: str) -> None:
    """Run memify — prune stale nodes, reweight by usage. Periodic (every Nth settle)."""
    try:
        await _post("/improve", {"dataset": dataset}, timeout=120.0)
    except Exception as e:  # noqa: BLE001
        logger.warning("memory.improve failed (ignored): %s", e)


async def forget(dataset: str) -> None:
    """Right-to-erasure (NDPR/GDPR) — wipe this identity's entire memory graph."""
    try:
        await _post("/forget", {"dataset": dataset}, timeout=60.0)
    except Exception as e:  # noqa: BLE001
        logger.warning("memory.forget failed (ignored): %s", e)
