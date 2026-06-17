"""Writes settlements to the OlaRegistry contract on 0G Chain via web3.py (async)."""

import logging

from web3 import AsyncWeb3
from web3.middleware import ExtraDataToPOAMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)

# Minimal ABI — only what we call.
REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "orderId", "type": "bytes32"},
            {"internalType": "string", "name": "direction", "type": "string"},
            {"internalType": "string", "name": "currency", "type": "string"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "string", "name": "storageHash", "type": "string"},
        ],
        "name": "logSettlement",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


def order_id_to_bytes32(order_uuid: str) -> bytes:
    """keccak256 of the internal order UUID — matches the contract's documented intent."""
    return AsyncWeb3.keccak(text=str(order_uuid))


async def log_to_registry(
    order_uuid: str,
    direction: str,
    currency: str,
    amount_cents: int,
    storage_hash: str,
) -> str:
    if not settings.REGISTRY_CONTRACT_ADDRESS or not settings.PRIVATE_KEY:
        raise RuntimeError("REGISTRY_CONTRACT_ADDRESS / PRIVATE_KEY not configured")

    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(settings.OG_CHAIN_RPC))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    acct = w3.eth.account.from_key(settings.PRIVATE_KEY)
    contract = w3.eth.contract(
        address=AsyncWeb3.to_checksum_address(settings.REGISTRY_CONTRACT_ADDRESS),
        abi=REGISTRY_ABI,
    )

    order_id = order_id_to_bytes32(order_uuid)
    nonce = await w3.eth.get_transaction_count(acct.address)
    tx = await contract.functions.logSettlement(
        order_id, direction, currency, amount_cents, storage_hash
    ).build_transaction(
        {
            "from": acct.address,
            "nonce": nonce,
            "chainId": settings.OG_CHAIN_ID,
        }
    )

    signed = acct.sign_transaction(tx)
    tx_hash = await w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = await w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    logger.info("logSettlement tx %s status=%s", receipt.transactionHash.hex(), receipt.status)
    return receipt.transactionHash.hex()
