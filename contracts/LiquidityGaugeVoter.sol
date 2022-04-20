// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "./StakedNoteRef.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface ILiquidityGauge {
    function deposit(uint256 value) external;

    function withdraw(uint256 value, bool claim_rewards) external;

    function claim_rewards() external;

    function balanceOf(address) external view returns (uint256);

    // curve & balancer use lp_token()
    function lp_token() external view returns (address);

    // angle use staking_token()
    function staking_token() external view returns (address);

    function reward_tokens(uint256 i) external view returns (address token);

    function reward_count() external view returns (uint256 nTokens);
}

interface ILiquidityGaugeController {
    function vote_for_gauge_weights(address gauge_addr, uint256 user_weight)
        external;

    function last_user_vote(address user, address gauge)
        external
        view
        returns (uint256);

    function vote_user_power(address user) external view returns (uint256);

    function gauge_types(address gauge) external view returns (int128);
}

/// @title Liquidity gauge voter, used to vote on the NOTE 80/20 liquidity gauge
/// @author Fei Protocol
abstract contract LiquidityGaugeVoter is StakedNoteRef {
    // Events
    event GaugeControllerChanged(
        address indexed oldController,
        address indexed newController
    );
    event GaugeVote(address indexed gauge, uint256 amount);

    /// @notice address of the gauge controller used for voting
    address public gaugeController;

    constructor(address _gaugeController) {
        gaugeController = _gaugeController;
    }

    /// @notice Set the gauge controller used for gauge weight voting
    /// @param _gaugeController the gauge controller address
    function setGaugeController(address _gaugeController)
        public
        onlyOwner
    {
        require(
            gaugeController != _gaugeController,
            "LiquidityGaugeVoter: same controller"
        );

        address oldController = gaugeController;
        gaugeController = _gaugeController;

        emit GaugeControllerChanged(oldController, gaugeController);
    }

    /// @notice Vote for a gauge's weight
    /// @param liquidityGauge liquidity gauge address
    /// @param weight gauge weight in BPS, 10000 BPS = 100%
    function voteForGaugeWeight(address liquidityGauge, uint256 weight)
        public
        onlyOwner
    {
        ILiquidityGaugeController(gaugeController).vote_for_gauge_weights(
            liquidityGauge,
            weight
        );

        emit GaugeVote(liquidityGauge, weight);
    }
}
