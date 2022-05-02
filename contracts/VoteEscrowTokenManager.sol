// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "./utils/BoringOwnable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../interfaces/notional/IStakedNote.sol";
import "../interfaces/balancer/IVeToken.sol";
import "../interfaces/balancer/IFeeDistributor.sol";

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
    event FeeDistributorUpdated(address newFeeDistributor);
    event VaultContractUpdated(address vaultContract);
    event TokenTransferred(uint256 amount);
    event RewardTokensClaimed(IERC20[] tokens, uint256[] amounts);

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

    /// @notice The fee distributor address
    IFeeDistributor public feeDistributor;

    /// @notice The vault contract address
    address public vaultContract;

    /// @notice VoteEscrowTokenManager token Snapshot Delegator PCV Deposit constructor
    /// @param _liquidityToken the token to lock for vote-escrow (BAL/ETH LP Token)
    /// @param _veToken the vote-escrowed token used in governance
    /// @param _lockDuration amount of time (in seconds) tokens will  be vote-escrowed for
    constructor(
        IERC20 _liquidityToken,
        IVeToken _veToken,
        IFeeDistributor _feeDistributor,
        IStakedNote _sNOTE,
        uint256 _lockDuration
    ) {
        liquidityToken = _liquidityToken;
        veToken = _veToken;
        feeDistributor = _feeDistributor;
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

    /// @notice Set the fee distributor address
    /// @param newFeeDistributor new VeToken address
    function setFeeDistributor(address newFeeDistributor) external onlyOwner {
        require(
            address(feeDistributor) != newFeeDistributor,
            "Same FeeDistributor"
        );

        feeDistributor = IFeeDistributor(newFeeDistributor);
        emit FeeDistributorUpdated(newFeeDistributor);
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

    /// @notice Allows the owner to transfer tokens to the treasury manager
    /// @param token token address
    /// @param dest destination address
    /// @param amount amount to transfer
    function withdrawToken(
        address token,
        address dest,
        uint256 amount
    ) external onlyOwner {
        if (amount == type(uint256).max)
            amount = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(dest, amount);
        emit TokenTransferred(amount);
    }

    /// @notice Claims reward tokens from the fee distributor
    /// @param tokens a list of tokens to claim
    function claimTokens(IERC20[] calldata tokens) external onlyOwner {
        uint256[] memory balancesBefore = new uint256[](tokens.length);
        for (uint256 i; i < tokens.length; i++) {
            balancesBefore[i] = tokens[i].balanceOf(address(this));
        }

        feeDistributor.claimTokens(address(this), tokens);

        uint256[] memory balancesTransferred = new uint256[](tokens.length);
        for (uint256 i; i < tokens.length; i++) {
            balancesTransferred[i] =
                tokens[i].balanceOf(address(this)) -
                balancesBefore[i];
        }

        emit RewardTokensClaimed(tokens, balancesTransferred);
    }

    /// @notice returns total balance of tokens, vote-escrowed or liquid.
    function totalTokensManaged() public view returns (uint256) {
        return
            liquidityToken.balanceOf(address(this)) +
            veToken.locked(address(this));
    }
}
