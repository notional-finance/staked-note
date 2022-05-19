// SPDX-License-Identifier: MIT
pragma solidity =0.8.11;

interface IStakedNote {
    function stakeAll() external;
    function owner() external view returns (address);
    function TREASURY_MANAGER_CONTRACT() external view returns (address);
    function NOTE() external view returns (address);
    function WETH() external view returns (address);
    function claimBAL() external;
}
