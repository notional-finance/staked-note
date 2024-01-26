// SPDX-License-Identifier: GPL-v3
pragma solidity >=0.7.6;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {TradeType} from "../trading/ITradingModule.sol";

interface IStrategyVault {
    /// @notice Parameters for trades
    struct TradeParams {
        /// @notice DEX ID
        uint16 dexId;
        /// @notice Trade type (i.e. Single/Batch)
        TradeType tradeType;
        /// @notice For dynamic trades, this field specifies the slippage percentage relative to
        /// the oracle price. For static trades, this field specifies the slippage limit amount.
        uint256 oracleSlippagePercentOrLimit;
        /// @notice DEX specific data
        bytes exchangeData;
    }

    /// @notice Single-sided reinvestment trading parameters
    struct SingleSidedRewardTradeParams {
        /// @notice Address of the token to sell (typically one of the reward tokens)
        address sellToken;
        /// @notice Address of the token to buy (typically one of the pool tokens)
        address buyToken;
        /// @notice Amount of tokens to sell
        uint256 amount;
        /// @notice Trade params
        TradeParams tradeParams;
    }

    function claimRewardTokens() external;
    function reinvestReward(
        SingleSidedRewardTradeParams[] calldata trades,
        uint256 minPoolClaim
    ) external returns (address rewardToken, uint256 amountSold, uint256 poolClaimAmount);
}
