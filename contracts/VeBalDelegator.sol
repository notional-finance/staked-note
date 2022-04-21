// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "./VoteEscrowTokenManager.sol";
import "./LiquidityGaugeVoter.sol";
import "./GovernorVoter.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/// @title 80-BAL-20-WETH BPT PCV Deposit
/// @author Fei Protocol
contract VeBalDelegator is
    VoteEscrowTokenManager,
    LiquidityGaugeVoter,
    GovernorVoter
{
    address public constant B_80BAL_20WETH =
        0x5c6Ee304399DBdB9C8Ef030aB642B10820DB8F56;
    address public constant VE_BAL = 0xC128a9954e6c874eA3d62ce62B468bA073093F25;
    address public constant BALANCER_GAUGE_CONTROLLER =
        0xC128468b7Ce63eA702C1f104D55A2566b13D3ABD;

    /// @notice veBAL token manager
    constructor()
        VoteEscrowTokenManager(
            ERC20(B_80BAL_20WETH), // liquid token
            IVeToken(VE_BAL), // vote-escrowed token
            365 * 86400 // vote-escrow time = 1 year
        )
        LiquidityGaugeVoter(BALANCER_GAUGE_CONTROLLER)
        GovernorVoter()
    {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), owner);
    }
}
