"""
0G Chain OrderRegistry writer.

web3.py is synchronous, so the signed send + receipt wait runs in a worker
thread to avoid blocking the event loop. HTTP egress goes through the standard
proxy (web3 uses requests under the hood), so this works from a firewalled
environment as long as the RPC is HTTPS.
"""

import anyio
from web3 import Web3

from app.core.config import settings

# Minimal ABI — just what we call/read.
REGISTRY_ABI = [
    {
        "type": "function",
        "name": "logSettlement",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "orderId", "type": "bytes32"},
            {"name": "direction", "type": "string"},
            {"name": "currency", "type": "string"},
            {"name": "amount", "type": "uint256"},
            {"name": "storageHash", "type": "string"},
        ],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "totalSettlements",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
]


async def log_to_registry(
    order_id_bytes: bytes,
    direction: str,
    currency: str,
    amount_cents: int,
    storage_hash: str,
) -> str:
    return await anyio.to_thread.run_sync(
        _log_sync, order_id_bytes, direction, currency, amount_cents, storage_hash
    )


def _log_sync(
    order_id_bytes: bytes,
    direction: str,
    currency: str,
    amount_cents: int,
    storage_hash: str,
) -> str:
    if not settings.REGISTRY_CONTRACT_ADDRESS:
        raise RuntimeError("REGISTRY_CONTRACT_ADDRESS not set — deploy the contract first.")

    w3 = Web3(Web3.HTTPProvider(settings.OG_CHAIN_RPC))
    acct = w3.eth.account.from_key(settings.DEPLOYER_PRIVATE_KEY)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(settings.REGISTRY_CONTRACT_ADDRESS),
        abi=REGISTRY_ABI,
    )

    tx = contract.functions.logSettlement(
        order_id_bytes, direction, currency, int(amount_cents), storage_hash
    ).build_transaction(
        {
            "from": acct.address,
            "nonce": w3.eth.get_transaction_count(acct.address),
            "chainId": settings.OG_CHAIN_ID,
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    # Normalize: hexbytes may or may not include the 0x prefix across versions.
    h = tx_hash.hex()
    return h if h.startswith("0x") else f"0x{h}"
