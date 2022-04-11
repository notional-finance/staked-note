// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.7.0;

interface Comptroller {
    function claimComp(address holder, address[] calldata ctokens) external;

    function compAccrued(address holder) external view returns (uint256);

    function getCompAddress() external view returns (address);
}
