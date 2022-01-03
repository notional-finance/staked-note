// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;
pragma abicoder v2;

interface NotionalTreasuryAction {
    function transferReserveToTreasury(address[] calldata assets)
        external
        returns (uint256[] memory);

    function setTreasuryManager(address manager) external;
}
