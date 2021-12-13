// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {BoringOwnable} from "./BoringOwnable.sol";
import {IVault, IAsset} from "interfaces/IVault.sol";

contract stNOTE is ERC20, ERC20Votes, BoringOwnable, Initializable, UUPSUpgradeable {
    IVault public immutable BALANCER_VAULT;
    ERC20 public immutable NOTE;
    ERC20 public immutable BALANCER_POOL_TOKEN;
    bytes32 public immutable NOTE_ETH_POOL_ID;

    /// @notice Maximum shotfall withdraw of 30%
    uint256 public constant MAX_SHORTFALL_WITHDRAW = 30;

    struct AccountCoolDown {
        uint32 coolDownExpirationTimestamp;
        uint224 maxBPTWithdraw;
    }

    /// @notice Number of seconds that need to pass before stNOTE can be redeemed
    uint32 public coolDownTimeInSeconds;

    /// @notice Mapping between stNOTE holders and their current cooldown status
    mapping(address => AccountCoolDown) public accountCoolDown;

    /// @notice Emitted when a cool down begins
    event CoolDownStarted(address account, uint256 expiration, uint256 maxPoolTokenWithdraw);

    constructor(
        IVault _balancerVault,
        bytes32 _noteETHPoolId,
        ERC20 _note
    ) 
        ERC20("Staked NOTE", "stNOTE")
        ERC20Permit("Staked NOTE")
        initializer { 
        // Validate that the pool exists
        (address poolAddress, /* */) = _balancerVault.getPool(_noteETHPoolId);
        require(poolAddress != address(0));
        // require(abi.encode(_note.symbol()) == abi.encode("NOTE"));

        NOTE = _note;
        NOTE_ETH_POOL_ID = _noteETHPoolId;
        BALANCER_VAULT = _balancerVault;
        BALANCER_POOL_TOKEN = ERC20(poolAddress);
    }

    function initialize(
        address _owner,
        uint32 _coolDownTimeInSeconds
    ) external initializer {
        coolDownTimeInSeconds = _coolDownTimeInSeconds;
        owner = _owner;
        emit OwnershipTransferred(address(0), _owner);
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}

    function setCoolDownTime(uint32 _coolDownTimeInSeconds) external onlyOwner {
        coolDownTimeInSeconds = _coolDownTimeInSeconds;
    }

    function mintFromBPT(uint256 bptAmount) external {
        BALANCER_POOL_TOKEN.transferFrom(msg.sender, address(this), bptAmount);
        _mint(msg.sender, bptAmount);
    }

    function mintFromNOTE(uint256 noteAmount) external {
        // User must set approval on the BalancerVault for NOTE. This is more convenient
        // because they may want to trade on Balancer as well. Does not require a second
        // approval on the stNOTE contract
        IAsset[] memory assets = new IAsset[](2);
        assets[0] = IAsset(address(0));
        assets[1] = IAsset(address(NOTE));
        uint256[] memory maxAmountsIn = new uint256[](2);
        maxAmountsIn[0] = 0;
        maxAmountsIn[1] = noteAmount;

        uint256 bptBefore = BALANCER_POOL_TOKEN.balanceOf(address(this));
        uint256 bptAmountOut = 0;

        // Will sell some NOTE for ETH to get the correct amount of BPT
        BALANCER_VAULT.joinPool(
            NOTE_ETH_POOL_ID,
            msg.sender,
            address(this), // stNOTE will receive the BPT
            IVault.JoinPoolRequest(
                assets,
                maxAmountsIn,
                abi.encode(
                    IVault.JoinKind.TOKEN_IN_FOR_EXACT_BPT_OUT,
                    bptAmountOut, // How do we calculate this?
                    1 // Token Index for NOTE
                ),
                false // Don't use internal balances
            )
        );

        uint256 bptAfter = BALANCER_POOL_TOKEN.balanceOf(address(this));

        // Balancer pool token amounts must increase
        _mint(msg.sender, bptAfter - bptBefore);
    }

    function startCoolDown() external {
        // Cannot start a cool down if there is already one in effect
        _checkIfCoolDownInEffect(msg.sender);
        uint256 expiration = _safe32(block.timestamp + coolDownTimeInSeconds);
        // Ensures that the account cannot accrue a larger pool token share during the cooldown period
        uint256 maxBPTWithdraw = getPoolTokenShare(this.balanceOf(msg.sender));

        accountCoolDown[msg.sender] = AccountCoolDown(_safe32(expiration), _safe224(maxBPTWithdraw));

        emit CoolDownStarted(msg.sender, expiration, maxBPTWithdraw);
    }

    function redeem(uint256 stNOTEAmount) external {
        AccountCoolDown memory coolDown = accountCoolDown[msg.sender];
        require(
            coolDown.coolDownExpirationTimestamp != 0 &&
            coolDown.coolDownExpirationTimestamp < block.timestamp,
            "Cool Down Not Expired"
        );

        uint256 bptToTransfer = _min(getPoolTokenShare(stNOTEAmount), coolDown.maxBPTWithdraw);
        BALANCER_POOL_TOKEN.transfer(msg.sender, bptToTransfer);

        // Reset the cool down back to zero so that the account must initiate it again to redeem
        delete accountCoolDown[msg.sender];

        _burn(msg.sender, stNOTEAmount);
    }

    function getPoolTokenShare(uint256 stNOTEAmount) public view returns (uint256 bptClaim) {
        uint256 bptBalance = BALANCER_POOL_TOKEN.balanceOf(address(this));
        // BPT and stNOTE are both in 18 decimal precision so no conversion required
        return (bptBalance * stNOTEAmount) / this.totalSupply();
    }

    function extractTokensForCollateralShortfall(uint256 bptTokenAmount) external onlyOwner {
        uint256 bptBalance = BALANCER_POOL_TOKEN.balanceOf(address(this));
        require(bptTokenAmount <= (bptBalance * MAX_SHORTFALL_WITHDRAW) / 100, "Over Max Shortfall Withdraw");
        BALANCER_POOL_TOKEN.transfer(msg.sender, bptTokenAmount);
    }

    /** Internal Methods **/

    function _checkIfCoolDownInEffect(address account) internal view {
        uint256 expiration = accountCoolDown[account].coolDownExpirationTimestamp;
        require(expiration == 0 || expiration < block.timestamp, "Cool Down Not Expired");
    }

    function _burn(address account, uint256 amount) internal override(ERC20, ERC20Votes) {
        // Handles event emission, balance update and total supply update
        ERC20Votes._burn(account, amount);
    }

    function _mint(address account, uint256 amount) internal override(ERC20, ERC20Votes) {
        // Cannot mint if a cooldown is already in effect
        _checkIfCoolDownInEffect(msg.sender);

        // Handles event emission, balance update and total supply update
        ERC20Votes._mint(account, amount);
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20) {
        // Cannot send or receive tokens if a cooldown is in effect
        // TODO: check if this restriction is necessary
        _checkIfCoolDownInEffect(from);
        _checkIfCoolDownInEffect(to);
    }

    function _afterTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20, ERC20Votes) {
        // Moves stNOTE checkpoints
        ERC20Votes._afterTokenTransfer(from, to, amount);
    }


    function _min(uint256 x, uint256 y) internal pure returns (uint256) {
        return x < y ? x : y;
    }

    function _safe32(uint256 x) internal pure returns (uint32) {
        require (x <= type(uint32).max);
        return uint32(x);
    }

    function _safe224(uint256 x) internal pure returns (uint224) {
        require (x <= type(uint224).max);
        return uint224(x);
    }
}