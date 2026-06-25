"""
Lightweight status push.

The MVP frontend polls GET /api/v1/sessions/{id}/order, so a "push" just means
persisting the latest webhook event onto the order row. Swap this for SSE or a
WebSocket later without touching the webhook handler.
"""


async def push_status_update(db, order, payload: dict) -> None:
    if order is None:
        return
    order.last_event = payload.get("event")
    order.last_event_message = payload.get("message")
    await db.flush()
