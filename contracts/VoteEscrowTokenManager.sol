// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "./utils/BoringOwnable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/notional/IStakedNote.sol";
import "../interfaces/balancer/IVeToken.sol";

/// @title Vote-escrowed Token Manager
/// Used to permanently lock tokens in a vote-escrow contract, and refresh
/// the lock duration as needed.
/// @author Fei Protocol
abstract contract VoteEscrowTokenManager is BoringOwnable {
    using SafeERC20 for IERC20;

    // Events
    event Lock(uint256 cummulativeTokensLocked, uint256 lockHorizon);
    event Unlock(uint256 tokensUnlocked);
    event LockDurationUpdated(uint256 newLockDuration);
    event LiquidityTokenUpdated(address newLiquidityToken);
    event VeTokenUpdated(address newVeToken);

    /// @notice Staked NOTE contract
    IStakedNote public immutable sNOTE;

    /// @notice One week, in seconds. Vote-locking is rounded down to weeks.
    uint256 private constant WEEK = 7 * 86400; // 1 week, in seconds

    /// @notice The lock duration of veTokens
    uint256 public lockDuration;

    /// @notice The vote-escrowed token address
    IVeToken public veToken;

    /// @notice The token address
    IERC20 public liquidityToken;

    /// @notice VoteEscrowTokenManager token Snapshot Delegator PCV Deposit constructor
    /// @param _liquidityToken the token to lock for vote-escrow (BAL/ETH LP Token)
    /// @param _veToken the vote-escrowed token used in governance
    /// @param _lockDuration amount of time (in seconds) tokens will  be vote-escrowed for
    constructor(
        IERC20 _liquidityToken,
        IVeToken _veToken,
        IStakedNote _sNOTE,
        uint256 _lockDuration
    ) {
        liquidityToken = _liquidityToken;
        veToken = _veToken;
        sNOTE = _sNOTE;
        lockDuration = _lockDuration;
    }

    /// @notice Set the amount of time tokens will be vote-escrowed for in lock() calls
    /// @param newLockDuration new lock duration
    function setLockDuration(uint256 newLockDuration) external onlyOwner {
        lockDuration = newLockDuration;
        emit LockDurationUpdated(newLockDuration);
    }

    /// @notice Set the BAL/ETH liquidity token address
    /// @param newLiquidityToken new liquidity token address
    function setLiquidityToken(address newLiquidityToken) external onlyOwner {
        require(
            address(liquidityToken) != newLiquidityToken,
            "Same liquidity token"
        );

        liquidityToken = IERC20(newLiquidityToken);
        emit LiquidityTokenUpdated(newLiquidityToken);
    }

    /// @notice Set the VeToken address
    /// @param newVeToken new VeToken address
    function setVeToken(address newVeToken) external onlyOwner {
        require(address(veToken) != newVeToken, "Same VeToken");

        veToken = IVeToken(newVeToken);
        emit VeTokenUpdated(newVeToken);
    }

    /// @notice Deposit tokens to get veTokens. Set lock duration to lockDuration.
    /// The only way to withdraw tokens will be to pause this contract
    /// for lockDuration and then call exitLock().
    function lock() external onlyOwner {
        uint256 tokenBalance = liquidityToken.balanceOf(address(this));
        uint256 locked = veToken.locked(address(this));
        uint256 lockHorizon = ((block.timestamp + lockDuration) / WEEK) * WEEK;

        // First lock
        if (tokenBalance != 0 && locked == 0) {
            liquidityToken.approve(address(veToken), tokenBalance);
            veToken.create_lock(tokenBalance, lockHorizon);
        }
        // Increase amount of tokens locked & refresh duration to lockDuration
        else if (tokenBalance != 0 && locked != 0) {
            liquidityToken.approve(address(veToken), tokenBalance);
            veToken.increase_amount(tokenBalance);
            if (veToken.locked__end(address(this)) != lockHorizon) {
                veToken.increase_unlock_time(lockHorizon);
            }
        }
        // No additional tokens to lock, just refresh duration to lockDuration
        else if (tokenBalance == 0 && locked != 0) {
            veToken.increase_unlock_time(lockHorizon);
        }
        // If tokenBalance == 0 and locked == 0, there is nothing to do.
        emit Lock(tokenBalance + locked, lockHorizon);
    }

    /// @notice Exit the veToken lock. For this function to be called and not
    /// revert, tokens had to be locked previously, and the contract must have
    /// been paused for lockDuration in order to prevent lock extensions
    /// by calling lock(). This function will recover tokens on the contract,
    /// which can then be moved by calling withdraw() as a PCVController if the
    /// contract is also a PCVDeposit, for instance.
    function exitLock() external onlyOwner {
        veToken.withdraw();

        emit Unlock(liquidityToken.balanceOf(address(this)));
    }


    /// @notice returns total balance of tokens, vote-escrowed or liquid.
    function totalTokensManaged() public view returns (uint256) {
        return
            liquidityToken.balanceOf(address(this)) +
            veToken.locked(address(this));
    }
}
