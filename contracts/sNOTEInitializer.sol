// SPDX-License-Identifier: MIT
pragma solidity =0.8.11;

import {BoringOwnable} from "./utils/BoringOwnable.sol";
import "@openzeppelin/contracts/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC20/extensions/ERC20VotesUpgradeable.sol";
import {IVault, IAsset} from "../interfaces/balancer/IVault.sol";
import "../interfaces/balancer/IWeightedPool.sol";
import "../interfaces/balancer/IPriceOracle.sol";
import "../interfaces/balancer/ILiquidityGauge.sol";
import "../interfaces/balancer/IBalancerMinter.sol";
import "./utils/BalancerUtils.sol";

contract sNOTEInitializer is
    ERC20VotesUpgradeable,
    BoringOwnable,
    UUPSUpgradeable,
    ReentrancyGuard
{
    using SafeERC20 for ERC20;

    IVault public immutable BALANCER_VAULT;
    ERC20 public immutable NOTE;
    ERC20 public immutable WETH;

    /// @notice Number of seconds that need to pass before sNOTE can be redeemed
    uint32 public coolDownTimeInSeconds;

    /// @notice Constructor sets immutable contract addresses
    constructor(
        IVault _balancerVault,
        bytes32 _noteETHPoolId,
        uint256 _wethIndex,
        uint256 _noteIndex
    ) initializer {
        BALANCER_VAULT = _balancerVault;
        // prettier-ignore
        (address[] memory tokens, /* */, /* */) = _balancerVault.getPoolTokens(_noteETHPoolId);

        WETH = ERC20(tokens[_wethIndex]);
        NOTE = ERC20(tokens[_noteIndex]);
    }

    function initialize(address _owner, uint32 _coolDownTimeInSeconds)
        external
        initializer
    {
        string memory _name = "Staked NOTE";
        string memory _symbol = "sNOTE";
        __ERC20_init(_name, _symbol);
        __ERC20Permit_init(_name);

        coolDownTimeInSeconds = _coolDownTimeInSeconds;
        owner = _owner;
        NOTE.approve(address(BALANCER_VAULT), type(uint256).max);
        WETH.approve(address(BALANCER_VAULT), type(uint256).max);

        emit OwnershipTransferred(address(0), _owner);
    }

    /// @notice Authorizes the DAO to upgrade this contract
    function _authorizeUpgrade(
        address /* newImplementation */
    ) internal override onlyOwner {}
}
