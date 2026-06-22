"""Privacy endpoint — right-to-erasure (NDPR/GDPR) for the Cognee memory layer.

Wipes the caller's entire memory graph. Works both logged-in (wipes the durable
`ola-user-{id}` dataset) and anonymous (wipes the session-scoped `ola-anon-{session_id}`).
Only touches Cognee memory — never the on-chain 0G audit trail (which is, by design, immutable).
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.dependencies import get_optional_user
from app.models.user import User
from app.services.memory import dataset_for_user, forget

router = APIRouter()


class ForgetMeRequest(BaseModel):
    session_id: str


@router.post("/privacy/forget-me")
async def forget_me(req: ForgetMeRequest, user: Optional[User] = Depends(get_optional_user)):
    try:
        uuid.UUID(str(req.session_id))
    except ValueError:
        return {"ok": False, "detail": "session_id must be a valid UUID"}
    dataset = dataset_for_user(user, req.session_id)
    await forget(dataset)
    return {"ok": True, "forgotten": dataset}
