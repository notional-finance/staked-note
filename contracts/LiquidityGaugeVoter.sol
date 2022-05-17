// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "./utils/BoringOwnable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/balancer/ILiquidityGaugeController.sol";
import "../interfaces/balancer/ILiquidityGauge.sol";
import "../interfaces/balancer/IBalancerMinter.sol";

/// @title Liquidity gauge voter, used to vote on the NOTE 80/20 liquidity gauge
/// @author Fei Protocol
abstract contract LiquidityGaugeVoter is BoringOwnable {
    using SafeERC20 for IERC20;

    IBalancerMinter public immutable BALANCER_MINTER;
    IERC20 public immutable BAL_TOKEN;

    // Events
    event GaugeControllerChanged(
        address indexed oldController,
        address indexed newController
    );
    event GaugeVote(address indexed gauge, uint256 amount);
    event GaugeTokensClaimed(IERC20[] tokens, uint256[] amounts);
    event BALTokenClaimed(uint256 amount);
    event TokenWithdrawal(address token, address to, uint256 amount);
    event TokenDeposit(address token, address from, uint256 amount);

    /// @notice address of the gauge controller used for voting
    address public gaugeController;

    mapping(address => mapping(address => uint256)) private tokenBalances;

    constructor(IBalancerMinter _balancerMinter, address _gaugeController) {
        BALANCER_MINTER = _balancerMinter;
        BAL_TOKEN = IERC20(_balancerMinter.getBalancerToken());
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

    function claimBAL(address liquidityGauge) external onlyOwner {
        uint256 balBefore = BAL_TOKEN.balanceOf(address(this));
        BALANCER_MINTER.mint(address(liquidityGauge));
        uint256 balAfter = BAL_TOKEN.balanceOf(address(this));
        uint256 claimAmount = balAfter - balBefore;
        emit BALTokenClaimed(claimAmount);
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

    /// @notice Returns the token balance
    /// @param token token address
    /// @param from source address
    /// @return token balance
    function getTokenBalance(address token, address from)
        external
        view
        returns (uint256)
    {
        return tokenBalances[from][token];
    }

    /// @notice Allows the owner withdraw tokens
    /// @param token token address
    /// @param to destination address
    /// @param amount amount to transfer
    function withdrawToken(
        address token,
        address to,
        uint256 amount
    ) external onlyOwner {
        if (amount == type(uint256).max) amount = tokenBalances[to][token];

        require(amount <= tokenBalances[to][token]);

        tokenBalances[to][token] -= amount;
        IERC20(token).safeTransfer(to, amount);

        emit TokenWithdrawal(token, to, amount);
    }

    /// @notice Allows the owner to deposit tokens
    /// @dev This is mainly used for boosting balancer LP tokens
    /// @param token token address
    /// @param from source address
    /// @param amount deposit amount
    function depositToken(
        address token,
        address from,
        uint256 amount
    ) external onlyOwner {
        uint256 balBefore = IERC20(token).balanceOf(address(this));
        if (amount > 0) {
            IERC20(token).safeTransferFrom(from, address(this), amount);
        }
        uint256 balAfter = IERC20(token).balanceOf(address(this));
        tokenBalances[from][token] += (balAfter - balBefore);
        emit TokenDeposit(token, from, amount);
    }
}
