"""Live on-chain stats from OlaRegistry on 0G Chain — public proof-of-traction."""

import logging
import time
from typing import Any

from web3 import AsyncWeb3
from web3.middleware import ExtraDataToPOAMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)

CHAIN_SCAN = "https://chainscan-galileo.0g.ai/address"
_CACHE_TTL_SEC = 60

_REGISTRY_READ_ABI = [
    {
        "inputs": [],
        "name": "totalSettlements",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "orderId", "type": "bytes32"},
            {"indexed": False, "internalType": "string", "name": "direction", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "currency", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "string", "name": "storageHash", "type": "string"},
        ],
        "name": "OrderSettled",
        "type": "event",
    },
]

_cache: dict[str, Any] = {"at": 0.0, "data": None}


def _empty_stats(reason: str | None = None) -> dict:
    return {
        "configured": False,
        "live": False,
        "total_settlements": 0,
        "total_volume_usd": 0.0,
        "corridors": [],
        "by_direction": {"onramp": 0, "offramp": 0},
        "contract_address": None,
        "contract_url": None,
        "error": reason,
    }


async def get_registry_stats() -> dict:
    """Aggregate settlement stats from OlaRegistry events. Cached briefly to spare RPC."""
    now = time.time()
    if _cache["data"] and now - _cache["at"] < _CACHE_TTL_SEC:
        return _cache["data"]

    if not settings.REGISTRY_CONTRACT_ADDRESS:
        return _empty_stats("REGISTRY_CONTRACT_ADDRESS not configured")

    try:
        w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(settings.OG_CHAIN_RPC))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        addr = AsyncWeb3.to_checksum_address(settings.REGISTRY_CONTRACT_ADDRESS)
        contract = w3.eth.contract(address=addr, abi=_REGISTRY_READ_ABI)

        total = int(await contract.functions.totalSettlements().call())
        logs = await contract.events.OrderSettled.get_logs(from_block=0, to_block="latest")

        by_direction: dict[str, int] = {"onramp": 0, "offramp": 0}
        corridor_map: dict[str, dict] = {}
        volume_cents = 0

        for entry in logs:
            args = entry["args"]
            direction = (args.get("direction") or "").lower()
            currency = (args.get("currency") or "").upper()
            amount = int(args.get("amount") or 0)
            volume_cents += amount

            if direction in by_direction:
                by_direction[direction] += 1

            if currency:
                row = corridor_map.setdefault(
                    currency,
                    {"currency": currency, "count": 0, "volume_usd": 0.0},
                )
                row["count"] += 1
                row["volume_usd"] += amount / 100.0

        corridors = sorted(corridor_map.values(), key=lambda r: (-r["count"], r["currency"]))

        data = {
            "configured": True,
            "live": True,
            "contract_address": settings.REGISTRY_CONTRACT_ADDRESS,
            "contract_url": f"{CHAIN_SCAN}/{settings.REGISTRY_CONTRACT_ADDRESS}",
            "total_settlements": total,
            "events_indexed": len(logs),
            "total_volume_usd": round(volume_cents / 100.0, 2),
            "corridors": corridors,
            "by_direction": by_direction,
            "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        _cache["data"] = data
        _cache["at"] = now
        return data
    except Exception as e:  # noqa: BLE001
        logger.exception("registry stats fetch failed")
        return _empty_stats(str(e))