// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "../interfaces/IVault.sol";
import "../interfaces/chainlink/KeeperCompatibleInterface.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

contract VotingPowerKeeper is KeeperCompatibleInterface {
    using SafeMath for uint256;

    bytes32 public constant NOTE_POOL_ID = 0x5f7fa48d765053f8dd85e052843e12d23e3d7bc50002000000000000000000c0;
    uint256 public constant EXECUTION_INTERVAL = 60 * 60 * 2;
    IVault public immutable BALANCER_VAULT;
    ITreasuryManager public immutable TREASURY_MANAGER;
    uint256 private lastExecutionTimestamp;

    constructor(IVault _balancerVault, ITreasuryManager _treasuryManager)
    {
        BALANCER_VAULT = _balancerVault;
        TREASURY_MANAGER = _treasuryManager;
    }

    function checkUpkeep(bytes calldata checkData)
        external
        returns (bool upkeepNeeded, bytes memory performData)
    {
        upkeepNeeded = block.timestamp >= lastExecutionTimestamp.add(EXECUTION_INTERVAL);
        performData = checkData;
    }

    function performUpkeep(bytes calldata performData) external {
        lastExecutionTimestamp = block.timestamp;
    }
}
