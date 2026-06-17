import httpx

from app.core.config import settings


def _auth_headers() -> dict:
    return {"x-sidecar-token": settings.SIDECAR_AUTH_TOKEN}


async def store_transaction_record(record: dict) -> str:
    """POST the audit record to the Node sidecar; return the 0G Storage root hash."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.STORAGE_SIDECAR_URL}/store",
            json={"record": record},
            headers=_auth_headers(),
        )
        resp.raise_for_status()
        return resp.json()["rootHash"]


async def fetch_transaction_record(root_hash: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(
            f"{settings.STORAGE_SIDECAR_URL}/record/{root_hash}", headers=_auth_headers()
        )
        resp.raise_for_status()
        return resp.json()["data"]
