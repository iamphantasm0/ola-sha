"""Privacy endpoint — right-to-erasure (NDPR/GDPR) for the Cognee memory layer.

Wipes the authenticated caller's durable memory graph (`ola-user-{id}`). The dataset is
derived from the verified token identity, NEVER from a client-supplied id — accepting an
arbitrary session_id as proof of ownership would be an IDOR (any caller could wipe anyone's
memory). Anonymous memory is session-scoped, non-PII, and ephemeral, so it has no erasure
endpoint; it lives only under the session UUID the client itself holds.

Only touches Cognee memory — never the on-chain 0G audit trail (which is, by design, immutable).
"""
from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.memory import dataset_for_user, forget

router = APIRouter()


@router.post("/privacy/forget-me")
async def forget_me(user: User = Depends(get_current_user)):
    dataset = dataset_for_user(user, "")  # derived from user.id only; body is not trusted
    await forget(dataset)
    return {"ok": True, "forgotten": dataset}
