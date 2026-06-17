// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

/// @title OlaRegistry
/// @notice Append-only on-chain settlement log for Ola crypto<->fiat exchange.
///         The backend wallet (owner) writes one record per fully-settled order,
///         linking the on-chain proof to the 0G Storage audit record.
contract OlaRegistry is Ownable {
    struct Settlement {
        string direction; // "onramp" | "offramp"
        string currency; // "NGN", "KES", etc.
        uint256 amount; // USD value in cents (200 USDT == 20000)
        string storageHash; // 0G Storage root hash of the full audit record
        uint256 settledAt; // block.timestamp when logged
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

    /// @notice Log a completed settlement. Called by the backend wallet after Paycrest confirms.
    /// @param orderId     keccak256 of our internal order UUID
    /// @param direction   "onramp" or "offramp"
    /// @param currency    fiat currency code
    /// @param amount      USD value in cents
    /// @param storageHash 0G Storage root hash of the full audit record
    function logSettlement(
        bytes32 orderId,
        string calldata direction,
        string calldata currency,
        uint256 amount,
        string calldata storageHash
    ) external onlyOwner {
        require(settlements[orderId].settledAt == 0, "Already logged");

        settlements[orderId] = Settlement({
            direction: direction,
            currency: currency,
            amount: amount,
            storageHash: storageHash,
            settledAt: block.timestamp
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
