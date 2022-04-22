// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "./utils/BoringOwnable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/balancer/ILiquidityGaugeController.sol";

/// @title Liquidity gauge voter, used to vote on the NOTE 80/20 liquidity gauge
/// @author Fei Protocol
abstract contract LiquidityGaugeVoter is BoringOwnable {
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
}
