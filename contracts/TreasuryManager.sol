// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {BoringOwnable} from "./utils/BoringOwnable.sol";
import {EIP1271Wallet} from "./utils/EIP1271Wallet.sol";
import {IVault, IAsset} from "interfaces/IVault.sol";
import {NotionalTreasuryAction} from "interfaces/NotionalTreasuryAction.sol";

contract TreasuryManager is BoringOwnable {
    NotionalTreasuryAction public immutable NOTIONAL;
    ERC20 public immutable NOTE;
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
    event AssetsHarvested(address[] assets, uint256[] amounts);

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

    /// @dev This contract is not currently upgradeable, we can make it so and remove the selfdestruct
    /// call if we like
    constructor(
        address _owner,
        address _manager,
        address _notional,
        IVault _balancerVault,
        bytes32 _noteETHPoolId,
        ERC20 _note,
        address _stNOTE,
        address _assetProxy
    ) {
        owner = _owner;
        manager = _manager;
        NOTIONAL = NotionalTreasuryAction(_notional);
        stNOTE = _stNOTE;
        NOTE = _note;
        BALANCER_VAULT = _balancerVault;
        NOTE_ETH_POOL_ID = _noteETHPoolId;
        ASSET_PROXY = _assetProxy;

        emit OwnershipTransferred(address(0), _owner);
        emit ManagementTransferred(address(0), _manager);
    }

    function approveToken(address token, uint256 amount) external onlyManager {
        IERC20(token).approve(ASSET_PROXY, amount);
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
    function harvestAssetsFromNotional(address[] calldata assets)
        external
        onlyManager
        refundGas
    {
        uint256[] memory amountsTransferred = NOTIONAL
            .transferReserveToTreasury(assets);
        emit AssetsHarvested(assets, amountsTransferred);
    }

    function investETHToBuyNOTE(uint256 ethAmount)
        external
        onlyManager
        refundGas
    {
        _investETHToBuyNOTE(ethAmount);
    }

    function _investETHToBuyNOTE(uint256 ethAmount) internal {
        // How do we calculate this?
        uint256 bptAmountOut = 0;
        IAsset[] memory assets = new IAsset[](2);
        assets[0] = IAsset(address(0));
        assets[1] = IAsset(address(NOTE));
        uint256[] memory maxAmountsIn = new uint256[](2);
        maxAmountsIn[0] = ethAmount;
        maxAmountsIn[1] = 0;

        // Will sell ETH to buy NOTE and transfer the BPT to the stNOTE holders
        BALANCER_VAULT.joinPool{value: ethAmount}(
            NOTE_ETH_POOL_ID,
            address(this),
            stNOTE, // stNOTE will receive the BPT
            IVault.JoinPoolRequest(
                assets,
                maxAmountsIn,
                abi.encode(
                    IVault.JoinKind.TOKEN_IN_FOR_EXACT_BPT_OUT,
                    bptAmountOut,
                    0 // Token Index for ETH
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
}
