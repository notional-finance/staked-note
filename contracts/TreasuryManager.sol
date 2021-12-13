// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import {BoringOwnable} from "./BoringOwnable.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IVault, IAsset} from "interfaces/IVault.sol";

contract TreasuryManager is BoringOwnable {
    NotionalTreasuryAction public immutable NOTIONAL;
    ERC20 public immutable NOTE;
    IVault public immutable BALANCER_VAULT;
    address public immutable stNOTE;
    bytes32 public immutable NOTE_ETH_POOL_ID;

    address public manager;
    uint32 public refundGasPrice;

    event ManagementTransferred(address prevManager, address newManager);
    event RefundGasPriceSet(uint32 prevRefundGasPrice, uint32 newRefundGasPrice);

    modifier onlyManager() {
        require(msg.sender == manager, "Ownable: caller is not the owner");
        _;
    }

    modifier refundGas() {
        uint256 startGas = gasleft();
        // Fetch this value from storage here so that it is accounted for when
        // we refund the manager for their gas price
        uint256 _refundGasPrice = refundGasPrice;

        _;

        uint256 usedGas = startGas - gasleft();
        address(this).call{value: usedGas * refundGasPrice}("");
    }

    constructor (
        address _owner,
        address _manager,
        address _notional,
        IVault _balancerVault,
        bytes32 _noteETHPoolId,
        ERC20 _note,
        address _stNOTE
    ) {
        owner = _owner;
        manager = _manager;
        NOTIONAL = NotionalTreasuryAction(_notional);
        stNOTE = _stNOTE;
        NOTE = _note;
        BALANCER_VAULT = _balancerVault;
        NOTE_ETH_POOL_ID = _noteETHPoolId;

        emit OwnershipTransferred(address(0), _owner);
        emit ManagementTransferred(address(0), _manager);
    }

    function setManager(address newManager) external onlyOwner {
        emit ManagementTransferred(manager, newManager);
        manager = newManager;
    }

    function setRefundGas(uint32 _refundGasPrice) external onlyOwner {
        emit RefundGasPriceSet(refundGasPrice, _refundGasPrice);
        refundGasPrice = _refundGasPrice;
    }

    function harvestReserveBalance(
        uint16 currencyId,
        uint256 amount,
        bytes calldata dexParameters
    ) external onlyManager refundGas {
        uint256 amountTransferred = NotionalTreasuryAction.transferReserveToTreasury(currencyId, amount);
        uint256 ethAmount = _tradeToETHOnDex(currencyId, amountTransferred, dexParameters);
        _investETHToBuyNOTE(ethAmount);
    }

    function harvestCompIncentives(
        bytes calldata dexParameters
    ) external onlyManager refundGas {
        uint256 amountTransferred = NotionalTreasuryAction.harvestCOMP();
        uint256 ethAmount = _tradeToETHOnDex();
        _investETHToBuyNOTE(ethAmount);
    }

    function harvestAaveIncentives(
        bytes calldata dexParameters
    ) external onlyManager refundGas {
        uint256 amountTransferred = NotionalTreasuryAction.harvestAAVE();
        uint256 ethAmount = _tradeToETHOnDex();
        _investETHToBuyNOTE(ethAmount);
    }

    function _investETHToBuyNOTE(
        uint256 ethAmount
    ) internal {
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
}