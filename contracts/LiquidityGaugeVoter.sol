// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "./utils/BoringOwnable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/balancer/ILiquidityGaugeController.sol";
import "../interfaces/balancer/ILiquidityGauge.sol";

/// @title Liquidity gauge voter, used to vote on the NOTE 80/20 liquidity gauge
/// @author Fei Protocol
abstract contract LiquidityGaugeVoter is BoringOwnable {
    // Events
    event GaugeControllerChanged(
        address indexed oldController,
        address indexed newController
    );
    event GaugeVote(address indexed gauge, uint256 amount);

    event GaugeTokensClaimed(IERC20[] tokens, uint256[] amounts);

    /// @notice address of the gauge controller used for voting
    address public gaugeController;

    constructor(address _gaugeController) {
        gaugeController = _gaugeController;
    }

    /// @notice Set the gauge controller used for gauge weight voting
    /// @param _gaugeController the gauge controller address
    function setGaugeController(address _gaugeController) public onlyOwner {
        require(gaugeController != _gaugeController, "Same gauge controller");

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

    /// @notice Claims reward tokens available for a given liquidity gauge
    /// @param liquidityGauge liquidity gauge address
    function claimGaugeTokens(address liquidityGauge) external onlyOwner {
        uint256 count = ILiquidityGauge(liquidityGauge).reward_count();
        IERC20[] memory tokens = new IERC20[](count);
        uint256[] memory balancesBefore = new uint256[](count);

        for (uint256 i; i < count; i++) {
            tokens[i] = IERC20(
                ILiquidityGauge(liquidityGauge).reward_tokens(i)
            );
            balancesBefore[i] = IERC20(tokens[i]).balanceOf(address(this));
        }

        ILiquidityGauge(liquidityGauge).claim_rewards();

        uint256[] memory balancesTransferred = new uint256[](count);
        for (uint256 i; i < count; i++) {
            balancesTransferred[i] =
                IERC20(tokens[i]).balanceOf(address(this)) -
                balancesBefore[i];
        }

        emit GaugeTokensClaimed(tokens, balancesTransferred);
    }
}
