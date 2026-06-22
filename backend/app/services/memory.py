"""
Memory service — Cognee integration for Ola (WeMakeDevs × Cognee hackathon).

Gives the agent persistent, per-user memory across sessions. Validated end-to-end on
2026-06-22 (spike) with a **fully GPT-free** stack:
  - LLM (entity/relationship extraction + recall synthesis): minimax-m3 on the 0G Compute
    router (OpenAI-compatible), reused from Ola's existing OG_COMPUTE_* settings.
  - Structured output: **BAML** (`STRUCTURED_OUTPUT_FRAMEWORK=baml`). Instructor's strict
    tool-calling mode rejects minimax (a reasoning model returns prose + <think>, not a clean
    tool call); BAML parses structure out of the text and works.
  - Embeddings: **local fastembed** (`BAAI/bge-small-en-v1.5`, 384-dim) — no API, no key.
  - Stores: file-based defaults (SQLite + LanceDB + Kuzu/Ladybug) under SYSTEM/DATA roots.

ARCHITECTURE BOUNDARY (do not violate): Cognee NEVER touches the state-gated tool firewall.
It only feeds read-only context into the system prompt — memory informs what Ola *says*, never
what Ola *does*. Every function degrades gracefully: on any failure, a missing `cognee`
install, or a brand-new user, the chat flow continues unaffected.

Docs: https://docs.cognee.ai
"""
import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

# --- These MUST be set in os.environ BEFORE `import cognee` (Cognee reads them at import). ---
os.environ.setdefault("TELEMETRY_DISABLED", "true")
os.environ.setdefault("COGNEE_LOG_FILE", "false")
os.environ.setdefault("COGNEE_SKIP_CONNECTION_TEST", "true")  # minimax is slow to first token
# Instructor can't parse minimax's reasoning output → use BAML (validated 2026-06-22).
os.environ.setdefault("STRUCTURED_OUTPUT_FRAMEWORK", "baml")
# File-based stores. On Railway, mount a volume at both paths (they must persist together).
os.environ.setdefault("SYSTEM_ROOT_DIRECTORY", os.getenv("COGNEE_SYSTEM_ROOT", "/app/.cognee_system"))
os.environ.setdefault("DATA_ROOT_DIRECTORY", os.getenv("COGNEE_DATA_ROOT", "/app/.data_storage"))
# BAML drives structured extraction on the SAME 0G endpoint Ola already uses.
os.environ.setdefault("BAML_LLM_PROVIDER", "openai-generic")
os.environ["BAML_LLM_ENDPOINT"] = settings.OG_COMPUTE_BASE_URL
os.environ["BAML_LLM_API_KEY"] = settings.OG_COMPUTE_API_KEY
os.environ["BAML_LLM_MODEL"] = settings.OG_COMPUTE_MODEL

try:
    import cognee  # noqa: E402  (must follow the env setup above)
except Exception as e:  # noqa: BLE001 — app must boot even if cognee isn't installed (e.g. local dev)
    cognee = None
    logger.warning("cognee unavailable — memory layer disabled: %s", e)

_configured = False


def _configure() -> bool:
    """Apply runtime config once. Returns False if cognee isn't available."""
    global _configured
    if cognee is None:
        return False
    if _configured:
        return True
    # litellm routes by model prefix: 'openai/<model>' + custom api_base = OpenAI-compatible.
    cognee.config.set("llm_provider", "custom")
    cognee.config.set("llm_model", f"openai/{settings.OG_COMPUTE_MODEL}")
    cognee.config.set("llm_endpoint", settings.OG_COMPUTE_BASE_URL)
    cognee.config.set("llm_api_key", settings.OG_COMPUTE_API_KEY)
    cognee.config.set("embedding_provider", "fastembed")
    cognee.config.set("embedding_model", "BAAI/bge-small-en-v1.5")
    cognee.config.set("embedding_dimensions", 384)
    cognee.config.set("vector_db_provider", "lancedb")
    _configured = True
    return True


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


async def remember_fact(dataset: str, fact: str) -> None:
    """Store a structured fact in a memory graph. PII must already be masked by the caller.
    Never raises — memory must never break the core flow."""
    if not _configure():
        return
    try:
        await cognee.remember(fact, dataset_name=dataset)
    except Exception as e:  # noqa: BLE001
        logger.warning("cognee.remember failed (ignored): %s", e)


async def recall_context(dataset: str, query: str, limit: int = 5) -> str:
    """Pull relevant memory for the current turn, formatted for the system prompt. Returns ""
    for a new/anonymous user, a missing cognee, or any failure — a safe, chat-unchanged default."""
    if not _configure():
        return ""
    try:
        results = await cognee.recall(query_text=query, datasets=[dataset])
    except Exception as e:  # noqa: BLE001
        logger.warning("cognee.recall failed (ignored): %s", e)
        return ""
    facts = [getattr(r, "text", "") for r in (results or []) if getattr(r, "text", "")]
    return "\n".join(f"- {f}" for f in facts[:limit])


async def improve_memory(dataset: str) -> None:
    """Run memify — prune stale nodes, reweight by usage. Call periodically (every Nth settle)."""
    if not _configure():
        return
    try:
        await cognee.improve(dataset=dataset)
    except Exception as e:  # noqa: BLE001
        logger.warning("cognee.improve failed (ignored): %s", e)


async def forget(dataset: str) -> None:
    """Right-to-erasure (NDPR/GDPR) — wipe this identity's entire memory graph."""
    if not _configure():
        return
    try:
        await cognee.forget(dataset=dataset)
    except Exception as e:  # noqa: BLE001
        logger.warning("cognee.forget failed (ignored): %s", e)
