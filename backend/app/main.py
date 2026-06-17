import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import chat, orders, webhooks
from app.core.db import engine
from app.models import Base
from app.services.reconciler import run_reconciler

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # MVP: create tables on startup. (Swap for Alembic migrations before production.)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Background poller detects settlement without a Paycrest webhook (one URL per account).
    stop = asyncio.Event()
    task = asyncio.create_task(run_reconciler(stop))
    try:
        yield
    finally:
        stop.set()
        await task


app = FastAPI(title="Ola API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP — tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"ok": True, "service": "ola-api"}
