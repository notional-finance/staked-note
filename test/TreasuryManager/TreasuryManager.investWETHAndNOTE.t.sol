// SPDX-License-Identifier: MIT
pragma solidity >=0.8.11;

import "forge-std/Test.sol";

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {TreasuryManager} from "../../contracts/TreasuryManager.sol";
import {WETH9} from "../../interfaces/WETH9.sol";
import {NotionalTreasuryAction} from "../../interfaces/notional/NotionalTreasuryAction.sol";
import {ITradingModule, Trade, TradeType, TokenPermissions, DexId} from "../../interfaces/trading/ITradingModule.sol";
import {IVault} from "../../interfaces/balancer/IVault.sol";

interface NotionalProxy {
    function owner() external returns (address);
}

contract InvestWETHAndNoteTest is Test {
    event AssetsInvested(uint256 wethAmount, uint256 noteAmount);
    event NoteBurned(uint256 amountBurned);
    NotionalProxy constant NOTIONAL = NotionalProxy(0x1344A36A1B56144C3Bc62E7757377D288fDE0369);
    TreasuryManager treasuryManager = TreasuryManager(0x53144559C0d4a3304e2DD9dAfBD685247429216d);

    ITradingModule TRADING_MODULE = ITradingModule(0x594734c7e06C3D483466ADBCe401C6Bd269746C8);
    WETH9 WETH = WETH9(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    IERC20 public constant NOTE = IERC20(0xCFEAead4947f0705A14ec42aC3D44129E1Ef3eD5);
    address NoteTreasury = 0x22341fB5D92D3d801144aA5A925F401A91418A05;
    bytes zeroXData = hex'415565b0000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000cfeaead4947f0705a14ec42ac3d44129e1ef3ed50000000000000000000000000000000000000000000000000de0b6b3a76400000000000000000000000000000000000000000000000000000000016af8ec189400000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000046000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000cfeaead4947f0705a14ec42ac3d44129e1ef3ed500000000000000000000000000000000000000000000000000000000000001400000000000000000000000000000000000000000000000000000000000000420000000000000000000000000000000000000000000000000000000000000042000000000000000000000000000000000000000000000000000000000000003e00000000000000000000000000000000000000000000000000de0b6b3a764000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000420000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000001942616c616e63657256320000000000000000000000000000000000000000000000000000000000000de0b6b3a76400000000000000000000000000000000000000000000000000000000016af8ec1894000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000001c0000000000000000000000000ba12222222228d8ba445958a75a0704d566bf2c800000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000160000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000205122e01d819e58bb2e22528c0d68d310f0aa6fd700020000000000000000016300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000cfeaead4947f0705a14ec42ac3d44129e1ef3ed5000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001c000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee0000000000000000000000000000000000000000000000000000000000000000869584cd0000000000000000000000001000000000000000000000000000000000000011000000000000000000000000000000003ae3cf5b91eeedc8cb1eccff5872de76';

    function _upgradeTreasuryManager() internal {
        TreasuryManager newTreasuryManger = new TreasuryManager(
            NotionalTreasuryAction(address(NOTIONAL)),
            WETH,
            TRADING_MODULE
        );

        vm.prank(treasuryManager.owner());
        treasuryManager.upgradeTo(address(newTreasuryManger));
    }

    function setUp() public {
        vm.createSelectFork(vm.envString("MAINNET_RPC_URL"), 19019090);
        _upgradeTreasuryManager();
    }

    function test_investWETHAndNOTE_WhenNoteBurnPercentIsZero() public {
        uint256 wethInvestAmount = 10e18;
        uint256 noteInvestAmount = 1000e8;
        Trade memory buyNoteTrade = Trade(
            TradeType.EXACT_IN_SINGLE,
            address(WETH),
            address(NOTE),
            0,
            0,
            block.timestamp + 1 days,
            bytes("")
        );
        deal(address(WETH), address(treasuryManager), wethInvestAmount);
        vm.prank(NoteTreasury);
        NOTE.transfer(address(treasuryManager), noteInvestAmount);

        vm.startPrank(treasuryManager.manager());
        vm.expectEmit();
        emit AssetsInvested(wethInvestAmount, noteInvestAmount);
        treasuryManager.investWETHAndNOTE(wethInvestAmount, noteInvestAmount, 0, buyNoteTrade);
    }

    function test_investWETHAndNOTE_WhenNoteBurnPercentIsNotZero() public {
        uint8 noteBurnPercent = 10;
        vm.prank(treasuryManager.owner());
        treasuryManager.setNoteBurnPercent(noteBurnPercent);

        uint256 wethInvestAmount = 10e18;
        uint256 noteInvestAmount = 1000e8;
        uint256 wethForNoteToBurn = wethInvestAmount * noteBurnPercent / 100;
        Trade memory buyNoteTrade = Trade(
            TradeType.EXACT_IN_SINGLE,
            address(WETH),
            address(NOTE),
            wethForNoteToBurn,
            0,
            block.timestamp + 1 days,
            zeroXData
        );
        deal(address(WETH), address(treasuryManager), wethInvestAmount);
        vm.prank(NoteTreasury);
        NOTE.transfer(address(treasuryManager), noteInvestAmount);
        // allow selling of WETH
        vm.prank(NOTIONAL.owner());
        TRADING_MODULE.setTokenPermissions(
            address(treasuryManager),
            address(WETH),
            TokenPermissions(
                true,
                uint32(1 << uint32(DexId.ZERO_EX)),
                uint32(1 << uint32(TradeType.EXACT_IN_SINGLE))
            )
        );

        // precalculated, burned ~ 19.5k of NOTE which at block height of 19019090 is worth ~ 1 eth
        uint256 noteBurned = 1948692979386;
        uint256 burnAddressNoteBalance = NOTE.balanceOf(0x000000000000000000000000000000000000dEaD);

        vm.startPrank(treasuryManager.manager());
        vm.expectEmit();
        emit NoteBurned(noteBurned);
        vm.expectEmit();
        emit AssetsInvested(wethInvestAmount - wethForNoteToBurn, noteInvestAmount);
        treasuryManager.investWETHAndNOTE(wethInvestAmount, noteInvestAmount, 0, buyNoteTrade);

        assertEq(burnAddressNoteBalance + noteBurned, NOTE.balanceOf(0x000000000000000000000000000000000000dEaD));
    }

}