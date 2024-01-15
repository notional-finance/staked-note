// SPDX-License-Identifier: MIT
pragma solidity =0.8.11;

import "@openzeppelin/contracts/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/proxy/utils/UUPSUpgradeable.sol";
import {BoringOwnable} from "./utils/BoringOwnable.sol";
import {TradeHandler} from "./utils/TradeHandler.sol";
import {IVault, IAsset} from "../interfaces/balancer/IVault.sol";
import {NotionalTreasuryAction} from "../interfaces/notional/NotionalTreasuryAction.sol";
import {WETH9} from "../interfaces/WETH9.sol";
import {ITradingModule, Trade} from "../interfaces/trading/ITradingModule.sol";
import "../interfaces/notional/IStakedNote.sol";
import "../interfaces/notional/IStrategyVault.sol";
import "./utils/BalancerUtils.sol";

contract TreasuryManager is
    BoringOwnable,
    Initializable,
    UUPSUpgradeable
{
    using SafeERC20 for IERC20;
    using TradeHandler for Trade;

    /// @notice precision used to limit the amount of NOTE price impact (1e8 = 100%)
    uint256 internal constant NOTE_PURCHASE_LIMIT_PRECISION = 1e8;

    // following constants are relevant only for mainnet
    IERC20 public constant NOTE = IERC20(0xCFEAead4947f0705A14ec42aC3D44129E1Ef3eD5);
    IStakedNote public constant sNOTE = IStakedNote(0x38DE42F4BA8a35056b33A746A6b45bE9B1c3B9d2);
    bytes32 public constant NOTE_ETH_POOL_ID = 0x5122e01d819e58bb2e22528c0d68d310f0aa6fd7000200000000000000000163;
    ERC20 public constant BALANCER_POOL_TOKEN = ERC20(0x5122E01D819E58BB2E22528c0D68D310f0AA6FD7);
    IVault public constant BALANCER_VAULT = IVault(0xBA12222222228d8Ba445958a75a0704d566BF2C8);
    uint256 public constant WETH_INDEX = 0;
    uint256 public constant NOTE_INDEX = 1;

    NotionalTreasuryAction public immutable NOTIONAL;
    WETH9 public immutable WETH;
    ITradingModule public immutable TRADING_MODULE;
    uint32 public constant MAXIMUM_COOL_DOWN_PERIOD_SECONDS = 30 days;

    /// @notice From IPriceOracle.getLargestSafeQueryWindow
    uint32 public constant MAX_ORACLE_WINDOW_SIZE = 122400;

    /// @notice Balancer token indexes
    /// Balancer requires token addresses to be sorted BAL#102

    address public manager;

    /// @notice This limit determines the maximum price impact (% increase from current oracle price)
    /// from joining the BPT pool with WETH
    uint256 public notePurchaseLimit;

    /// @notice Number of seconds that need to pass before another investWETHAndNOTE can be called
    uint32 public coolDownTimeInSeconds;
    uint32 public lastInvestTimestamp;

    /// @notice Window for time weighted oracle price
    uint32 public priceOracleWindowInSeconds;

    event ManagementTransferred(address prevManager, address newManager);
    event AssetsHarvested(uint16[] currencies, uint256[] amounts);
    event AssetInterestHarvested(uint16[] currencies);
    event NOTEPurchaseLimitUpdated(uint256 purchaseLimit);
    event TradeExecuted(
        address indexed sellToken,
        address indexed buyToken,
        uint256 sellAmount,
        uint256 buyAmount
    );

    /// @notice Emitted when cool down time is updated
    event InvestmentCoolDownUpdated(uint256 newCoolDownTimeSeconds);
    event AssetsInvested(uint256 wethAmount, uint256 noteAmount);

    /// @notice Emitted when price oracle window is updated
    event PriceOracleWindowUpdated(uint256 _priceOracleWindowInSeconds);

    event VaultRewardTokensClaimed(address indexed vault, IERC20[] rewardTokens, uint256[] claimedBalances);

    event VaultRewardReinvested(
        address indexed vault,
        address indexed rewardToken,
        uint256 amountSold,
        uint256 poolClaimAmount
    );
    error InvalidChain();

    /// @dev Restricted methods for the treasury manager
    modifier onlyManager() {
        require(msg.sender == manager, "Unauthorized");
        _;
    }

    modifier onlyOnMainnet() {
        uint chainId;
        assembly {
            chainId := chainid()
        }
        if (chainId != 1) {
          revert InvalidChain();
        }
        _;
    }

    constructor(
        NotionalTreasuryAction _notional,
        WETH9 _weth,
        ITradingModule _tradingModule
    ) initializer {
        uint chainId;
        assembly {
            chainId := chainid()
        }
        if (chainId == 1) {
            // Balancer will revert if pool is not found
            (address poolAddress, /* */) = BALANCER_VAULT.getPool(NOTE_ETH_POOL_ID);
            require(poolAddress == address(BALANCER_POOL_TOKEN), "1");

            (address[] memory poolTokens,,) = BALANCER_VAULT.getPoolTokens(NOTE_ETH_POOL_ID);
            require(poolTokens[WETH_INDEX] == address(_weth), "2");
            require(poolTokens[NOTE_INDEX] == address(NOTE), "3");
        }

        NOTIONAL = NotionalTreasuryAction(_notional);
        WETH = _weth;
        TRADING_MODULE = _tradingModule;
    }

    function initialize(
        address _owner,
        address _manager,
        uint32 _coolDownTimeInSeconds
    ) external initializer {
        owner = _owner;
        manager = _manager;
        coolDownTimeInSeconds = _coolDownTimeInSeconds;
        emit OwnershipTransferred(address(0), _owner);
        emit ManagementTransferred(address(0), _manager);
    }

    function approveBalancer() external onlyOwner onlyOnMainnet {
        NOTE.safeApprove(address(BALANCER_VAULT), type(uint256).max);
        IERC20(address(WETH)).safeApprove(
            address(BALANCER_VAULT),
            type(uint256).max
        );
    }

    function setNOTEPurchaseLimit(uint256 purchaseLimit) external onlyOwner onlyOnMainnet {
        require(
            purchaseLimit <= NOTE_PURCHASE_LIMIT_PRECISION,
            "purchase limit is too high"
        );
        notePurchaseLimit = purchaseLimit;
        emit NOTEPurchaseLimitUpdated(purchaseLimit);
    }

    function withdraw(address token, uint256 amount) external onlyOwner {
        if (amount == type(uint256).max)
            amount = IERC20(token).balanceOf(address(this));
        if (amount > 0) IERC20(token).safeTransfer(msg.sender, amount);
    }

    function wrapToWETH() external onlyManager {
        WETH.deposit{value: address(this).balance}();
    }

    function setManager(address newManager) external onlyOwner {
        emit ManagementTransferred(manager, newManager);
        manager = newManager;
    }

    function claimBAL() external onlyManager onlyOnMainnet {
        sNOTE.claimBAL();
    }

    function claimVaultRewardTokens(address vault) external onlyManager {
        IStrategyVault(vault).claimRewardTokens();
    }

    function reinvestVaultReward(
        address vault,
        IStrategyVault.SingleSidedRewardTradeParams[][] calldata tradesPerRewardToken,
        uint256[] calldata minPoolClaims
    ) external onlyManager returns (
        address[] memory rewardTokens,
        uint256[] memory amountsSold,
        uint256[] memory poolClaimAmounts
    ) {
        rewardTokens = new address[](tradesPerRewardToken.length);
        amountsSold = new uint256[](tradesPerRewardToken.length);
        poolClaimAmounts = new uint256[](tradesPerRewardToken.length);

        for (uint256 i = 0; i < tradesPerRewardToken.length; i++) {
          (rewardTokens[i], amountsSold[i], poolClaimAmounts[i]) =
            IStrategyVault(vault).reinvestReward(tradesPerRewardToken[i], minPoolClaims[i]);
          emit VaultRewardReinvested(vault, rewardTokens[i], amountsSold[i], poolClaimAmounts[i]);
        }
    }

    /*** Manager Functionality  ***/

    /// @dev Will need to add a this method as a separate action behind the notional proxy
    function harvestAssetsFromNotional(uint16[] calldata currencies)
        external
        onlyManager
    {
        uint256[] memory amountsTransferred = NOTIONAL
            .transferReserveToTreasury(currencies);
        emit AssetsHarvested(currencies, amountsTransferred);
    }

    function harvestAssetInterestFromNotional(uint16[] calldata currencies)
        external
        onlyManager
    {
        NOTIONAL.harvestAssetInterest(currencies);
        emit AssetInterestHarvested(currencies);
    }

    /// @notice Updates the required cooldown time to invest
    function setCoolDownTime(uint32 _coolDownTimeInSeconds) external onlyOwner {
        require(_coolDownTimeInSeconds <= MAXIMUM_COOL_DOWN_PERIOD_SECONDS);
        coolDownTimeInSeconds = _coolDownTimeInSeconds;
        emit InvestmentCoolDownUpdated(_coolDownTimeInSeconds);
    }

    /// @notice Updates the price oracle window
    function setPriceOracleWindow(uint32 _priceOracleWindowInSeconds)
        external
        onlyOwner
    {
        require(_priceOracleWindowInSeconds <= MAX_ORACLE_WINDOW_SIZE);
        priceOracleWindowInSeconds = _priceOracleWindowInSeconds;
        emit PriceOracleWindowUpdated(_priceOracleWindowInSeconds);
    }

    function executeTrade(Trade calldata trade, uint8 dexId) 
        external onlyManager returns (uint256 amountSold, uint256 amountBought) {
        require(trade.sellToken != address(WETH));
        require(trade.buyToken == address(WETH) || trade.buyToken == address(NOTE));

        (amountSold, amountBought) = trade._executeTrade(dexId, TRADING_MODULE);
        emit TradeExecuted(trade.sellToken, trade.buyToken, amountSold, amountBought);
    }

    /// @notice Allows treasury manager to invest WETH and NOTE into the Balancer pool
    /// @param wethAmount amount of WETH to transfer into the Balancer pool
    /// @param noteAmount amount of NOTE to transfer into the Balancer pool
    /// @param minBPT slippage parameter to prevent front running
    function investWETHAndNOTE(
        uint256 wethAmount,
        uint256 noteAmount,
        uint256 minBPT
    ) external onlyManager onlyOnMainnet {
        uint32 blockTime = _safe32(block.timestamp);
        require(
            lastInvestTimestamp + coolDownTimeInSeconds < blockTime,
            "Investment Cooldown"
        );
        lastInvestTimestamp = blockTime;

        IAsset[] memory assets = new IAsset[](2);
        assets[WETH_INDEX] = IAsset(address(WETH));
        assets[NOTE_INDEX] = IAsset(address(NOTE));
        uint256[] memory maxAmountsIn = new uint256[](2);
        maxAmountsIn[WETH_INDEX] = wethAmount;
        maxAmountsIn[NOTE_INDEX] = noteAmount;

        // Gets the balancer time weighted average price denominated in ETH
        uint256 noteOraclePrice = BalancerUtils.getTimeWeightedOraclePrice(
            address(BALANCER_POOL_TOKEN),
            IPriceOracle.Variable.PAIR_PRICE,
            uint256(priceOracleWindowInSeconds)
        );

        BALANCER_VAULT.joinPool(
            NOTE_ETH_POOL_ID,
            address(this),
            address(sNOTE), // sNOTE will receive the BPT
            IVault.JoinPoolRequest(
                assets,
                maxAmountsIn,
                abi.encode(
                    IVault.JoinKind.EXACT_TOKENS_IN_FOR_BPT_OUT,
                    maxAmountsIn,
                    minBPT // Apply minBPT to prevent front running
                ),
                false // Don't use internal balances
            )
        );

        // Make sure the donated BPT is staked
        sNOTE.stakeAll();

        uint256 noteSpotPrice = _getNOTESpotPrice();

        // Calculate the max spot price based on the purchase limit
        uint256 maxPrice = noteOraclePrice +
            (noteOraclePrice * notePurchaseLimit) /
            NOTE_PURCHASE_LIMIT_PRECISION;

        require(noteSpotPrice <= maxPrice, "price impact is too high");

        emit AssetsInvested(wethAmount, noteAmount);
    }

    function _getNOTESpotPrice() public view returns (uint256) {
        // prettier-ignore
        (
            /* address[] memory tokens */,
            uint256[] memory balances,
            /* uint256 lastChangeBlock */
        ) = BALANCER_VAULT.getPoolTokens(NOTE_ETH_POOL_ID);

        // increase NOTE precision to 1e18
        uint256 noteBal = balances[NOTE_INDEX] * 1e10;

        // We need to multiply the numerator by 1e18 to preserve enough
        // precision for the division
        // NOTEWeight = 0.8
        // ETHWeight = 0.2
        // SpotPrice = (ETHBalance / 0.2 * 1e18) / (NOTEBalance / 0.8)
        // SpotPrice = (ETHBalance * 5 * 1e18) / (NOTEBalance * 1.25)
        // SpotPrice = (ETHBalance * 5 * 1e18) / (NOTEBalance * 125 / 100)

        return (balances[WETH_INDEX] * 5 * 1e18) / ((noteBal * 125) / 100);
    }

    function _safe32(uint256 x) internal pure returns (uint32) {
        require(x <= type(uint32).max);
        return uint32(x);
    }

    function _authorizeUpgrade(
        address /* newImplementation */
    ) internal override onlyOwner {}
}
