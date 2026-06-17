"""Status delivery.

MVP uses frontend polling of GET /api/v1/orders/{id} as the source of truth — the DB
holds canonical state. This stub just logs; it exists so webhook code reads cleanly and
a real-time transport (SSE/WebSocket) can be slotted in later without touching callers.
"""

import logging

logger = logging.getLogger(__name__)


async def push_status_update(session_id, payload: dict) -> None:
    logger.info("status[%s]: %s", session_id, payload)
