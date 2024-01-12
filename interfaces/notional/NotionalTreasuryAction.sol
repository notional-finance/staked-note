// SPDX-License-Identifier: MIT
pragma solidity =0.8.11;
pragma abicoder v2;

interface NotionalTreasuryAction {
    function harvestAssetInterest(uint16[] calldata currencies) external;

    function transferReserveToTreasury(uint16[] calldata currencies)
        external
        returns (uint256[] memory);

    function setTreasuryManager(address manager) external;
}
