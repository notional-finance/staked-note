// SPDX-License-Identifier: MIT
pragma solidity =0.8.11;

interface sNoteProxy {
    function getImplementation() external view returns (address);
    function upgradeTo(address newImplementation) external;
    function upgradeToAndCall(address newImplementation, bytes memory data) external payable;
}