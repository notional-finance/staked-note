// SPDX-License-Identifier: MIT
pragma solidity >=0.8.11;

import "forge-std/Test.sol";

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {TreasuryManager} from "../../contracts/TreasuryManager.sol";
import {WETH9} from "../../interfaces/WETH9.sol";
import {NotionalTreasuryAction} from "../../interfaces/notional/NotionalTreasuryAction.sol";
import {ITradingModule, Trade} from "../../interfaces/trading/ITradingModule.sol";
import {IVault} from "../../interfaces/balancer/IVault.sol";

interface NotionalProxy {
    function owner() external returns (address);
}

abstract contract TreasuryManagerTest is Test {
    NotionalProxy constant NOTIONAL = NotionalProxy(0x1344A36A1B56144C3Bc62E7757377D288fDE0369);
    TreasuryManager treasuryManager = TreasuryManager(0x53144559C0d4a3304e2DD9dAfBD685247429216d);

    ITradingModule TRADING_MODULE;
    WETH9 WETH;

    function _fork() internal virtual;

    function _upgradeTreasuryManager() internal {
        vm.startPrank(treasuryManager.owner());
        TreasuryManager newTreasuryManger = new TreasuryManager(
            NotionalTreasuryAction(address(NOTIONAL)),
            WETH,
            TRADING_MODULE
        );

        treasuryManager.upgradeTo(address(newTreasuryManger));
    }

    function setUp() public {
        _fork();
    }

    function test_storage_VariablesNotChangedAfterUpgrade() public {
        uint32 maximumCoolDownPeriodSeconds = treasuryManager.MAXIMUM_COOL_DOWN_PERIOD_SECONDS();
        uint32 maxOracleWindowSize = treasuryManager.MAX_ORACLE_WINDOW_SIZE();

        address manager = treasuryManager.manager();
        uint256 notPurchaseLimit = treasuryManager.notePurchaseLimit();
        uint32 coolDownTimeInSeconds = treasuryManager.coolDownTimeInSeconds();
        uint32 lastInvestTimestamp = treasuryManager.lastInvestTimestamp();
        uint32 priceOracleWindowInSeconds = treasuryManager.priceOracleWindowInSeconds();

        _upgradeTreasuryManager();

        assertEq(maximumCoolDownPeriodSeconds, treasuryManager.MAXIMUM_COOL_DOWN_PERIOD_SECONDS(), "1");
        assertEq(maxOracleWindowSize, treasuryManager.MAX_ORACLE_WINDOW_SIZE(), "2");
        assertEq(manager, treasuryManager.manager(), "3");
        assertEq(notPurchaseLimit, treasuryManager.notePurchaseLimit(), "4");
        assertEq(coolDownTimeInSeconds, treasuryManager.coolDownTimeInSeconds(), "5");
        assertEq(lastInvestTimestamp, treasuryManager.lastInvestTimestamp(), "6");
        assertEq(priceOracleWindowInSeconds, treasuryManager.priceOracleWindowInSeconds(), "7");
    }

}

contract TreasuryManagerTestArbitrum is TreasuryManagerTest {
    function _fork() internal override {
        WETH = WETH9(0x82aF49447D8a07e3bd95BD0d56f35241523fBab1);
        TRADING_MODULE = ITradingModule(0xBf6B9c5608D520469d8c4BD1E24F850497AF0Bb8);
        vm.createSelectFork(vm.envString("ARBITRUM_RPC_URL"), 170729487);
    }

    function test_approveBalancer_ShouldFailIfNotOnMainnet() public {
        _upgradeTreasuryManager();

        vm.startPrank(treasuryManager.owner());
        vm.expectRevert(TreasuryManager.InvalidChain.selector);
        treasuryManager.approveBalancer();
    }

    function test_setNOTEPurchaseLimit_ShouldFailIfNotOnMainnet() public {
        _upgradeTreasuryManager();

        vm.startPrank(treasuryManager.owner());
        vm.expectRevert(TreasuryManager.InvalidChain.selector);
        treasuryManager.setNOTEPurchaseLimit(1e8);
    }

    function test_investWETHAndNOTE_ShouldFailIfNotOnMainnet() public {
        _upgradeTreasuryManager();

        vm.startPrank(treasuryManager.manager());
        Trade memory trade;
        vm.expectRevert(TreasuryManager.InvalidChain.selector);
        treasuryManager.investWETHAndNOTE(1e18, 1e18, 0, trade);
    }
}

contract TreasuryManagerTestMainnet is TreasuryManagerTest {
    function _fork() internal override {
        WETH = WETH9(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
        TRADING_MODULE = ITradingModule(0x594734c7e06C3D483466ADBCe401C6Bd269746C8);
        vm.createSelectFork(vm.envString("MAINNET_RPC_URL"), 19013495);
    }

    function test_approveBalancer_ShouldNotFailWithInvalidChainIfOnMainnet() public {
        _upgradeTreasuryManager();

        vm.startPrank(treasuryManager.owner());
        vm.expectRevert("SafeERC20: approve from non-zero to non-zero allowance");
        treasuryManager.approveBalancer();
    }

    function test_setNOTEPurchaseLimit_ShouldNotFailWithInvalidChainIfOnMainnet() public {
        _upgradeTreasuryManager();

        vm.startPrank(treasuryManager.owner());
        treasuryManager.setNOTEPurchaseLimit(1e8);
    }
}