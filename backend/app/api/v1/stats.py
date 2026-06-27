"""Public on-chain stats — proof-of-traction from OlaRegistry."""

from fastapi import APIRouter

from app.services.registry_stats import get_registry_stats

router = APIRouter()


@router.get("/stats/registry")
async def registry_stats():
    """Live totals from OlaRegistry on 0G Chain: settlements, volume, corridors."""
    return await get_registry_stats()