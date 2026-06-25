import httpx

from app.core.config import settings


async def store_transaction_record(record: dict) -> str:
    """POST the audit record to the Node sidecar; return the 0G Storage root hash."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{settings.STORAGE_SIDECAR_URL}/store", json={"record": record}
        )
        r.raise_for_status()
        return r.json()["rootHash"]


async def fetch_transaction_record(root_hash: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(f"{settings.STORAGE_SIDECAR_URL}/record/{root_hash}")
        r.raise_for_status()
        return r.json().get("data")
