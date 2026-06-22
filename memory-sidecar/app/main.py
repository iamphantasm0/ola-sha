"""
Memory sidecar — Cognee wrapped in a tiny HTTP service so its heavy/newer deps stay isolated
from the Ola backend (mirrors the storage-sidecar pattern). Only the backend calls it, over the
internal network, authenticated with x-sidecar-token.

Validated config (spike 2026-06-22), fully GPT-free:
  - LLM (extraction): minimax-m3 on the 0G Compute router (OG_COMPUTE_* env, OpenAI-compatible).
  - Structured output: BAML (STRUCTURED_OUTPUT_FRAMEWORK=baml) — Instructor rejects the reasoning
    model's prose output; BAML parses it.
  - Embeddings: local fastembed (BAAI/bge-small-en-v1.5, 384-dim) — no API key.
  - Stores: file-based (SQLite + LanceDB + Kuzu) under the SYSTEM/DATA roots (a mounted volume).
"""
import os
import re

# --- env MUST be set before `import cognee` ---
os.environ.setdefault("TELEMETRY_DISABLED", "true")
os.environ.setdefault("COGNEE_LOG_FILE", "false")
os.environ.setdefault("COGNEE_SKIP_CONNECTION_TEST", "true")  # minimax slow to first token
os.environ.setdefault("STRUCTURED_OUTPUT_FRAMEWORK", "baml")
os.environ.setdefault("SYSTEM_ROOT_DIRECTORY", os.getenv("COGNEE_SYSTEM_ROOT", "/app/.cognee_system"))
os.environ.setdefault("DATA_ROOT_DIRECTORY", os.getenv("COGNEE_DATA_ROOT", "/app/.data_storage"))

OG_BASE = os.environ["OG_COMPUTE_BASE_URL"]
OG_MODEL = os.environ["OG_COMPUTE_MODEL"]
OG_KEY = os.environ["OG_COMPUTE_API_KEY"]
os.environ.setdefault("BAML_LLM_PROVIDER", "openai-generic")
os.environ["BAML_LLM_ENDPOINT"] = OG_BASE
os.environ["BAML_LLM_API_KEY"] = OG_KEY
os.environ["BAML_LLM_MODEL"] = OG_MODEL

import cognee  # noqa: E402
from fastapi import Depends, FastAPI, Header, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402

cognee.config.set("llm_provider", "custom")
cognee.config.set("llm_model", f"openai/{OG_MODEL}")
cognee.config.set("llm_endpoint", OG_BASE)
cognee.config.set("llm_api_key", OG_KEY)
cognee.config.set("embedding_provider", "fastembed")
cognee.config.set("embedding_model", "BAAI/bge-small-en-v1.5")
cognee.config.set("embedding_dimensions", 384)
cognee.config.set("vector_db_provider", "lancedb")

AUTH_TOKEN = os.environ.get("SIDECAR_AUTH_TOKEN", "")

app = FastAPI(title="Ola Memory Sidecar", version="1.0.0")


async def require_token(x_sidecar_token: str = Header(default="")):
    if not AUTH_TOKEN or x_sidecar_token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")


class RememberBody(BaseModel):
    dataset: str
    fact: str


class RecallBody(BaseModel):
    dataset: str
    query: str
    limit: int = 5


class DatasetBody(BaseModel):
    dataset: str


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/remember", dependencies=[Depends(require_token)])
async def remember(body: RememberBody):
    await cognee.remember(body.fact, dataset_name=body.dataset)
    return {"ok": True}


# only_context=True skips the slow LLM synthesis (~15s) and returns retrieved graph context
# (~3s). We parse the node-content blocks into clean fact lines for prompt injection.
_BLOCK = re.compile(r"__node_content_start__\n(.*?)\n__node_content_end__", re.DOTALL)


def _clean_facts(text: str, limit: int) -> list[str]:
    facts: list[str] = []
    for block in _BLOCK.findall(text or ""):
        fact = " ".join(block.split())
        if len(fact.split()) >= 4 and fact not in facts:  # drop bare node-name/type nodes
            facts.append(fact)
    return facts[:limit]


@app.post("/recall", dependencies=[Depends(require_token)])
async def recall(body: RecallBody):
    results = await cognee.recall(query_text=body.query, datasets=[body.dataset], only_context=True, top_k=8)
    raw = "\n".join((getattr(r, "text", "") or "") for r in (results or []))
    facts = _clean_facts(raw, body.limit)
    return {"context": "\n".join(f"- {f}" for f in facts)}


@app.post("/improve", dependencies=[Depends(require_token)])
async def improve(body: DatasetBody):
    await cognee.improve(dataset=body.dataset)
    return {"ok": True}


@app.post("/forget", dependencies=[Depends(require_token)])
async def forget(body: DatasetBody):
    await cognee.forget(dataset=body.dataset)
    return {"ok": True}
