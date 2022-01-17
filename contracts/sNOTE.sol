// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import {BoringOwnable} from "./utils/BoringOwnable.sol";
import "@openzeppelin/contracts/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC20/extensions/ERC20VotesUpgradeable.sol";
import "@openzeppelin-upgradeable/contracts/token/ERC20/ERC20Upgradeable.sol";
import {IVault, IAsset} from "interfaces/IVault.sol";
import "interfaces/IWeightedPool.sol";

contract sNOTE is ERC20Upgradeable, ERC20VotesUpgradeable, BoringOwnable, UUPSUpgradeable {
    using SafeERC20 for ERC20;

    IVault public immutable BALANCER_VAULT;
    ERC20 public immutable NOTE;
    ERC20 public immutable BALANCER_POOL_TOKEN;
    ERC20 public immutable WETH;
    bytes32 public immutable NOTE_ETH_POOL_ID;

    /// @notice Maximum shotfall withdraw of 30%
    uint256 public constant MAX_SHORTFALL_WITHDRAW = 30;

    /// @notice Tracks an account's cool down time
    struct AccountCoolDown {
        uint32 coolDownExpirationTimestamp;
        uint224 maxBPTWithdraw;
    }

    /// @notice Number of seconds that need to pass before sNOTE can be redeemed
    uint32 public coolDownTimeInSeconds;

    /// @notice Mapping between sNOTE holders and their current cooldown status
    mapping(address => AccountCoolDown) public accountCoolDown;

    /// @notice Emitted when a cool down begins
    event CoolDownStarted(address account, uint256 expiration, uint256 maxPoolTokenWithdraw);

    /// @notice Emitted when a cool down ends
    event CoolDownEnded(address account);

    /// @notice Emitted when cool down time is updated
    event GlobalCoolDownUpdated(uint256 newCoolDownTimeSeconds);

    /// @notice Constructor sets immutable contract addresses
    constructor(
        IVault _balancerVault,
        bytes32 _noteETHPoolId,
        ERC20 _note,
        ERC20 _weth
    ) initializer { 
        // Validate that the pool exists
        (address poolAddress, /* */) = _balancerVault.getPool(_noteETHPoolId);
        require(poolAddress != address(0));

        WETH = _weth;
        NOTE = _note;
        NOTE_ETH_POOL_ID = _noteETHPoolId;
        BALANCER_VAULT = _balancerVault;
        BALANCER_POOL_TOKEN = ERC20(poolAddress);
    }

    /// @notice Initializes sNOTE ERC20 metadata and owner
    function initialize(
        address _owner,
        uint32 _coolDownTimeInSeconds
    ) external initializer {
        string memory _name = "Staked NOTE";
        string memory _symbol = "sNOTE";
        __ERC20_init(_name, _symbol);
        __ERC20Permit_init(_name);

        coolDownTimeInSeconds = _coolDownTimeInSeconds;
        owner = _owner;
        NOTE.safeApprove(address(BALANCER_VAULT), type(uint256).max);

        emit OwnershipTransferred(address(0), _owner);
    }

    /** Governance Methods **/

    /// @notice Authorizes the DAO to upgrade this contract
    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}

    /// @notice Updates the required cooldown time to redeem
    function setCoolDownTime(uint32 _coolDownTimeInSeconds) external onlyOwner {
        coolDownTimeInSeconds = _coolDownTimeInSeconds;
        emit GlobalCoolDownUpdated(_coolDownTimeInSeconds);
    }

    /// @notice Allows the DAO to extract up to 30% of the BPT tokens during a collateral shortfall event
    function extractTokensForCollateralShortfall(uint256 requestedWithdraw) external onlyOwner {
        uint256 bptBalance = BALANCER_POOL_TOKEN.balanceOf(address(this));
        uint256 maxBPTWithdraw = (bptBalance * MAX_SHORTFALL_WITHDRAW) / 100;
        // Do not allow a withdraw of more than the MAX_SHORTFALL_WITHDRAW percentage. Specifically don't
        // revert here since there may be a delay between when governance issues the token amount and when
        // the withdraw actually occurs.
        uint256 bptExitAmount = requestedWithdraw > maxBPTWithdraw ? maxBPTWithdraw : requestedWithdraw;

        IAsset[] memory assets = new IAsset[](2);
        assets[0] = IAsset(address(WETH));
        assets[1] = IAsset(address(NOTE));
        uint256[] memory minAmountsOut = new uint256[](2);
        minAmountsOut[0] = 0;
        minAmountsOut[1] = 0;

        BALANCER_VAULT.exitPool(
            NOTE_ETH_POOL_ID,
            address(this),
            payable(owner), // Owner will receive the NOTE and WETH
            IVault.ExitPoolRequest(
                assets,
                minAmountsOut,
                abi.encode(
                    IVault.ExitKind.EXACT_BPT_IN_FOR_TOKENS_OUT,
                    bptExitAmount
                ),
                false // Don't use internal balances
            )
        );
    }

    /// @notice Allows the DAO to set the swap fee on the BPT
    function setSwapFeePercentage(uint256 swapFeePercentage) external onlyOwner {
        IWeightedPool(address(BALANCER_POOL_TOKEN)).setSwapFeePercentage(swapFeePercentage);
    }

    /** User Methods **/

    /// @notice Mints sNOTE from the underlying BPT token. Will receive 1 sNOTE per BPT.
    /// @param bptAmount is the amount of BPT to transfer from the msg.sender.
    function mintFromBPT(uint256 bptAmount) external {
        BALANCER_POOL_TOKEN.safeTransferFrom(msg.sender, address(this), bptAmount);
        _mint(msg.sender, bptAmount);
    }

    /// @notice Mints sNOTE from some amount of NOTE tokens. User will receive 1 sNOTE per underlying
    /// BPT token minted
    /// @param noteAmount amount of NOTE to transfer into the sNOTE contract
    function mintFromNOTE(uint256 noteAmount) external {
        // Transfer the NOTE balance into sNOTE first
        NOTE.safeTransferFrom(msg.sender, address(this), noteAmount);

        IAsset[] memory assets = new IAsset[](2);
        assets[0] = IAsset(address(0));
        assets[1] = IAsset(address(NOTE));
        uint256[] memory maxAmountsIn = new uint256[](2);
        maxAmountsIn[0] = 0;
        maxAmountsIn[1] = noteAmount;

        uint256 bptBefore = BALANCER_POOL_TOKEN.balanceOf(address(this));
        // Will sell some NOTE for ETH to get the correct amount of BPT
        BALANCER_VAULT.joinPool(
            NOTE_ETH_POOL_ID,
            address(this),
            address(this), // sNOTE will receive the BPT
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

        uint256 bptAfter = BALANCER_POOL_TOKEN.balanceOf(address(this));

        // Balancer pool token amounts must increase
        _mint(msg.sender, bptAfter - bptBefore);
    }

    /// @notice Stops a cool down for the sender
    function stopCoolDown() public {
        // Reset the cool down back to zero so that the account must initiate it again to redeem
        delete accountCoolDown[msg.sender];
        emit CoolDownEnded(msg.sender);
    }

    /// @notice Begins a cool down period for the sender, this is required to redeem tokens
    function startCoolDown() external {
        // Cannot start a cool down if there is already one in effect
        _checkIfCoolDownInEffect(msg.sender);
        uint256 expiration = _safe32(block.timestamp + coolDownTimeInSeconds);
        // Ensures that the account cannot accrue a larger pool token share during the cooldown period
        uint256 maxBPTWithdraw = getPoolTokenShare(this.balanceOf(msg.sender));

        accountCoolDown[msg.sender] = AccountCoolDown(_safe32(expiration), _safe224(maxBPTWithdraw));

        emit CoolDownStarted(msg.sender, expiration, maxBPTWithdraw);
    }

    /// @notice Redeems some amount of sNOTE to underlying BPT tokens (which can then be sold for
    /// NOTE or ETH). An account must have passed its cool down expiration before they can redeem
    /// @param sNOTEAmount amount of sNOTE to redeem
    function redeem(uint256 sNOTEAmount) external {
        AccountCoolDown memory coolDown = accountCoolDown[msg.sender];
        require(
            coolDown.coolDownExpirationTimestamp != 0 &&
            coolDown.coolDownExpirationTimestamp < block.timestamp,
            "Cool Down Not Expired"
        );

        uint256 bptToTransfer = _min(getPoolTokenShare(sNOTEAmount), coolDown.maxBPTWithdraw);
        BALANCER_POOL_TOKEN.safeTransfer(msg.sender, bptToTransfer);

        // Reset the cool down back to zero so that the account must initiate it again to redeem
        stopCoolDown();

        _burn(msg.sender, sNOTEAmount);
    }

    /** External View Methods **/

    /// @notice Returns how many Balancer pool tokens an sNOTE token amount has a claim on
    function getPoolTokenShare(uint256 sNOTEAmount) public view returns (uint256 bptClaim) {
        uint256 bptBalance = BALANCER_POOL_TOKEN.balanceOf(address(this));
        // BPT and sNOTE are both in 18 decimal precision so no conversion required
        return (bptBalance * sNOTEAmount) / totalSupply();
    }

    /// @notice Returns the pool token share of a specific account
    function poolTokenShareOf(address account) public view returns (uint256 bptClaim) {
        return getPoolTokenShare(balanceOf(account));
    }

    // TODO: override getPastVotes
    // Not clear how we should calculate the voting weight of sNOTE, may need to talk to chainlink
    // to get a weighted NOTE claim on the underlying

    /** Internal Methods **/

    function _checkIfCoolDownInEffect(address account) internal view {
        uint256 expiration = accountCoolDown[account].coolDownExpirationTimestamp;
        require(expiration == 0 || expiration < block.timestamp, "Cool Down Not Expired");
    }

    function _burn(address account, uint256 amount) internal override(ERC20Upgradeable, ERC20VotesUpgradeable) {
        // Handles event emission, balance update and total supply update
        super._burn(account, amount);
    }

    function _mint(address account, uint256 amount) internal override(ERC20Upgradeable, ERC20VotesUpgradeable) {
        // TODO: this mint is not correct...

        // Cannot mint if a cooldown is already in effect
        _checkIfCoolDownInEffect(msg.sender);

        // Handles event emission, balance update and total supply update
        super._mint(account, amount);
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20Upgradeable) {
        // Cannot send tokens if a cooldown is in effect
        _checkIfCoolDownInEffect(from);
        // If the `to` account has a cool down in effect, they cannot redeem more than `maxBPTWithdraw`
        // which is their poolTokenShare at the time the cool down started. They can receive more tokens
        // here but they will not be able to redeem them unless they start a new cool down.

        super._beforeTokenTransfer(from, to, amount);
    }

    function _afterTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20Upgradeable, ERC20VotesUpgradeable) {
        // Moves sNOTE checkpoints
        super._afterTokenTransfer(from, to, amount);
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