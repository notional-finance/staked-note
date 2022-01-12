// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts/proxy/utils/UUPSUpgradeable.sol";
import {BoringOwnable} from "./utils/BoringOwnable.sol";
import {EIP1271Wallet} from "./utils/EIP1271Wallet.sol";
import {IVault, IAsset} from "interfaces/balancer/IVault.sol";
import {NotionalTreasuryAction} from "interfaces/notional/NotionalTreasuryAction.sol";
import {WETH9} from "interfaces/WETH9.sol";

contract TreasuryManager is BoringOwnable, Initializable, UUPSUpgradeable {
    using SafeERC20 for IERC20;

    NotionalTreasuryAction public immutable NOTIONAL;
    WETH9 public immutable WETH;
    IERC20 public immutable NOTE;
    IVault public immutable BALANCER_VAULT;
    address public immutable stNOTE;
    bytes32 public immutable NOTE_ETH_POOL_ID;
    address public immutable ASSET_PROXY;

    address public manager;
    uint32 public refundGasPrice;

    event ManagementTransferred(address prevManager, address newManager);
    event RefundGasPriceSet(
        uint32 prevRefundGasPrice,
        uint32 newRefundGasPrice
    );
    event AssetsHarvested(uint16[] currencies, uint256[] amounts);
    event COMPHarvested(address[] ctokens, uint256 amount);

    /// @dev Restricted methods for the treasury manager
    modifier onlyManager() {
        require(msg.sender == manager, "Unauthorized");
        _;
    }

    /// @notice Will refund gas to the treasury manager
    modifier refundGas() {
        uint256 startGas = gasleft();
        // Fetch this value from storage here so that it is accounted for when
        // we refund the manager for their gas price
        // TODO: also investigate using the chainlink gas price oracle instead
        // https://data.chain.link/ethereum/mainnet/gas/fast-gas-gwei
        uint256 _refundGasPrice = refundGasPrice;

        _;

        uint256 usedGas = startGas - gasleft();
        address(this).call{value: usedGas * refundGasPrice}("");
    }

    constructor(
        NotionalTreasuryAction _notional,
        WETH9 _weth,
        IVault _balancerVault,
        bytes32 _noteETHPoolId,
        IERC20 _note,
        address _stNOTE,
        address _assetProxy
    ) initializer {
        NOTIONAL = NotionalTreasuryAction(_notional);
        stNOTE = _stNOTE;
        NOTE = _note;
        WETH = _weth;
        BALANCER_VAULT = _balancerVault;
        NOTE_ETH_POOL_ID = _noteETHPoolId;
        ASSET_PROXY = _assetProxy;
    }

    function initialize(address _owner, address _manager) external initializer {
        owner = _owner;
        manager = _manager;
        emit OwnershipTransferred(address(0), _owner);
        emit ManagementTransferred(address(0), _manager);
    }

    function approveToken(address token, uint256 amount) external onlyOwner {
        IERC20(token).approve(ASSET_PROXY, amount);
    }

    function withdraw(address token, uint256 amount) external onlyOwner {
        if (amount == type(uint256).max)
            amount = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(owner, amount);
    }

    function wrapToWETH() external onlyManager {
        WETH.deposit{value: address(this).balance}();
    }

    function setManager(address newManager) external onlyOwner {
        emit ManagementTransferred(manager, newManager);
        manager = newManager;
    }

    /// @dev investigate replacing this with the chainlink gas oracle
    function setRefundGasPrice(uint32 _refundGasPrice) external onlyOwner {
        emit RefundGasPriceSet(refundGasPrice, _refundGasPrice);
        refundGasPrice = _refundGasPrice;
    }

    /*** Manager Functionality  ***/

    /// @dev Will need to add a this method as a separate action behind the notional proxy
    function harvestAssetsFromNotional(uint16[] calldata currencies)
        external
        onlyManager
        refundGas
    {
        uint256[] memory amountsTransferred = NOTIONAL
            .transferReserveToTreasury(currencies);
        emit AssetsHarvested(currencies, amountsTransferred);
    }

    function harvestCOMPFromNotional(address[] calldata ctokens)
        external
        onlyManager
        refundGas
    {
        uint256 amountTransferred = NOTIONAL.claimCOMP(ctokens);
        emit COMPHarvested(ctokens, amountTransferred);
    }

    function investWETHToBuyNOTE(uint256 wethAmount)
        external
        onlyManager
        refundGas
    {
        _investWETHToBuyNOTE(wethAmount);
    }

    function _investWETHToBuyNOTE(uint256 wethAmount) internal {
        IAsset[] memory assets = new IAsset[](2);
        assets[0] = IAsset(address(WETH));
        assets[1] = IAsset(address(NOTE));
        uint256[] memory maxAmountsIn = new uint256[](2);
        maxAmountsIn[0] = wethAmount;
        maxAmountsIn[1] = 0;

        BALANCER_VAULT.joinPool(
            NOTE_ETH_POOL_ID,
            address(this),
            stNOTE, // stNOTE will receive the BPT
            IVault.JoinPoolRequest(
                assets,
                maxAmountsIn,
                abi.encode(
                    IVault.JoinKind.EXACT_TOKENS_IN_FOR_BPT_OUT,
                    maxAmountsIn,
                    0 // Accept however much BPT the pool will give us
                ),
                false // Don't use internal balances
            )
        );
    }

    function isValidSignature(bytes calldata data, bytes calldata signature)
        external
        view
        returns (bytes4)
    {
        return EIP1271Wallet.isValidSignature(data, signature, manager);
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
}
