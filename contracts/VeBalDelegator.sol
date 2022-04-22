// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "./VoteEscrowTokenManager.sol";
import "./LiquidityGaugeVoter.sol";
import "./GovernorVoter.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "../interfaces/balancer/ILiquidityGauge.sol";
import "../interfaces/balancer/ILiquidityGaugeController.sol";
import "../interfaces/balancer/IVeToken.sol";
import "../interfaces/notional/IStakedNote.sol";

/// @title 80-BAL-20-WETH BPT PCV Deposit
/// @author Fei Protocol
contract VeBalDelegator is
    VoteEscrowTokenManager,
    LiquidityGaugeVoter,
    GovernorVoter
{
    uint256 private constant YEAR = 365 * 86400; // 1 year, in seconds

    /// @notice veBAL token manager
    constructor(
        ERC20 _liquidityToken,
        IVeToken _veBal,
        address _gaugeController,
        IStakedNote _sNOTE
    )
        VoteEscrowTokenManager(_liquidityToken, _veBal, _sNOTE, YEAR)
        LiquidityGaugeVoter(gaugeController)
        GovernorVoter()
    {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), owner);
    }
}
