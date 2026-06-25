// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title OlaRegistry
 * @notice Append-only on-chain settlement log for Ola — an AI-powered
 *         crypto <-> fiat exchange demo by Vela Labs (Zero Cup 2026).
 *
 *         One row is written per fully-settled Paycrest order. The full
 *         human-readable audit record lives in 0G Storage; this contract
 *         anchors a tamper-evident pointer (the storage root hash) on
 *         0G Chain so any third party can independently verify a settlement.
 *
 *         Deployed to 0G Chain (Galileo testnet, chainId 16602 / Aristotle
 *         mainnet, chainId 16661). Only the backend settlement wallet (owner)
 *         may write.
 */
contract OlaRegistry is Ownable {

    struct Settlement {
        string  direction;      // "onramp" | "offramp"
        string  currency;       // "NGN", "KES", "UGX", "TZS", "MWK", "BRL"
        uint256 amount;         // USD value in cents (200 USDT => 20000)
        string  storageHash;    // 0G Storage root hash of the audit record
        uint256 settledAt;      // block.timestamp at log time
    }

    mapping(bytes32 => Settlement) public settlements;
    bytes32[] public allOrderIds;

    event OrderSettled(
        bytes32 indexed orderId,
        string direction,
        string currency,
        uint256 amount,
        string storageHash
    );

    constructor(address _owner) Ownable(_owner) {}

    /**
     * @notice Log a completed settlement. Called by the backend wallet after
     *         Paycrest confirms `payment_order.settled`.
     * @param orderId     sha256 of our internal order UUID (as bytes32)
     * @param direction   "onramp" or "offramp"
     * @param currency    fiat currency code
     * @param amount      USD value in cents
     * @param storageHash 0G Storage root hash of the full audit record
     */
    function logSettlement(
        bytes32 orderId,
        string calldata direction,
        string calldata currency,
        uint256 amount,
        string calldata storageHash
    ) external onlyOwner {
        require(settlements[orderId].settledAt == 0, "Already logged");

        // NOTE: no trailing comma after the final field — the original scope
        // had `settledAt: block.timestamp,` which is a Solidity syntax error.
        settlements[orderId] = Settlement({
            direction:   direction,
            currency:    currency,
            amount:      amount,
            storageHash: storageHash,
            settledAt:   block.timestamp
        });

        allOrderIds.push(orderId);
        emit OrderSettled(orderId, direction, currency, amount, storageHash);
    }

    function getSettlement(bytes32 orderId) external view returns (Settlement memory) {
        return settlements[orderId];
    }

    function totalSettlements() external view returns (uint256) {
        return allOrderIds.length;
    }
}
