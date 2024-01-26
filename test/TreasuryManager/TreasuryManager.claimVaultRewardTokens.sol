// SPDX-License-Identifier: MIT
pragma solidity >=0.8.11;

import "forge-std/Test.sol";

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {TreasuryManager} from "../../contracts/TreasuryManager.sol";
import {WETH9} from "../../interfaces/WETH9.sol";
import {NotionalTreasuryAction} from "../../interfaces/notional/NotionalTreasuryAction.sol";
import {ITradingModule} from "../../interfaces/trading/ITradingModule.sol";
import {IVault} from "../../interfaces/balancer/IVault.sol";

interface NotionalProxy {
    function owner() external returns (address);
}

contract ClaimVaultRewardTokensTest is Test {
    NotionalProxy constant NOTIONAL = NotionalProxy(0x1344A36A1B56144C3Bc62E7757377D288fDE0369);
    TreasuryManager treasuryManager = TreasuryManager(0x53144559C0d4a3304e2DD9dAfBD685247429216d);

    WETH9 constant WETH = WETH9(0x82aF49447D8a07e3bd95BD0d56f35241523fBab1);
    ITradingModule constant TRADING_MODULE = ITradingModule(0xBf6B9c5608D520469d8c4BD1E24F850497AF0Bb8);

    string ARBITRUM_RPC_URL = vm.envString("ARBITRUM_RPC_URL");
    uint256 ARBITRUM_FORK_BLOCK = 162581350;

    // data generate by rewards bot
    bytes reinvestData = hex'e800d5590000000000000000000000003df035433cface65b6d68b77cc916085d020c8b800000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000002b000000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000011000000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000007c00000000000000000000000000000000000000000000000000000000000000900000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002dce5edd95c049000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000012f54e26c193e00000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000628415565b0000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b800000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab100000000000000000000000000000000000000000000000002dce5edd95c04900000000000000000000000000000000000000000000000000001402eef00538900000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000003e000000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000034000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b800000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab100000000000000000000000000000000000000000000000000000000000001400000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000002c000000000000000000000000000000000000000000000000002dce5edd95c04900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000025375736869537761700000000000000000000000000000000000000000000000000000000000000002dce5edd95c04900000000000000000000000000000000000000000000000000001402eef005389000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000001b02da8cb0d097eb8d57a175b88c7d8b4799750600000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000002000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b800000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab10000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000002000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b8000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee0000000000000000000000000000000000000000000000000000000000000000869584cd00000000000000000000000010000000000000000000000000000000000000110000000000000000000000000000000093a0602a2335c6ab5330ab1f58ac8cb1000000000000000000000000000000000000000000000000000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b8000000000000000000000000ade4a71bb62bec25154cfc7e6ff49a513b491e8100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b8000000000000000000000000ec70dcb4a1efa46b8f2d97c310c9c4790ba5ffa800000000000000000000000000000000000000000000000002dce5edd95c04900000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001132ccee273c000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000668415565b0000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b8000000000000000000000000ec70dcb4a1efa46b8f2d97c310c9c4790ba5ffa800000000000000000000000000000000000000000000000002dce5edd95c0490000000000000000000000000000000000000000000000000000122766899b31200000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000042000000000000000000000000000000000000000000000000000000000000000150000000000000000000000000000000000000000000000000000000000000040000000000000000000000000000000000000000000000000000000000000038000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b8000000000000000000000000ec70dcb4a1efa46b8f2d97c310c9c4790ba5ffa8000000000000000000000000000000000000000000000000000000000000014000000000000000000000000000000000000000000000000000000000000003400000000000000000000000000000000000000000000000000000000000000340000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000002dce5edd95c0490000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003400000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000012556e697377617056330000000000000000000000000000000000000000000000000000000000000002dce5edd95c0490000000000000000000000000000000000000000000000000000122766899b312000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000e592427a0aece92de3edee1f18e0157c05861564000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000042040d1edc9569d4bab2d15287dc5a4f10f56a56b800271082af49447d8a07e3bd95bd0d56f35241523fbab10001f4ec70dcb4a1efa46b8f2d97c310c9c4790ba5ffa80000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000002000000000000000000000000040d1edc9569d4bab2d15287dc5a4f10f56a56b8000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee0000000000000000000000000000000000000000000000000000000000000000869584cd0000000000000000000000001000000000000000000000000000000000000011000000000000000000000000000000009b39b085fe6ee6921a4ae06a5ca016ac0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000009c00000000000000000000000000000000000000000000000000000000000000b000000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005243d5e810723bd000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000066da36bd4c2000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000828415565b00000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b00000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab100000000000000000000000000000000000000000000000005243d5e810723bd00000000000000000000000000000000000000000000000000006c9100e4422200000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000005e0000000000000000000000000000000000000000000000000000000000000001500000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b00000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab100000000000000000000000000000000000000000000000000000000000001400000000000000000000000000000000000000000000000000000000000000500000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000004c000000000000000000000000000000000000000000000000005243d5e810723bd00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000500000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000001942616c616e636572563200000000000000000000000000000000000000000000000000000000000005243d5e810723bd00000000000000000000000000000000000000000000000000006c9100e44222000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000002a0000000000000000000000000ba12222222228d8ba445958a75a0704d566bf2c8000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000002200000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000e049b2de7d214070893c038299a57bac5acb8b8a340001000000000000000004be00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001409791d590788598535278552eecd4b211bfc790cb00000000000000000000049800000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b0000000000000000000000005979d7b546e38e414f7e9822514be443a480052900000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab10000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000e00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000020000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee0000000000000000000000000000000000000000000000000000000000000000869584cd00000000000000000000000010000000000000000000000000000000000000110000000000000000000000000000000010abd228ce9b0d30b8f399937d3492d70000000000000000000000000000000000000000000000000000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b000000000000000000000000ade4a71bb62bec25154cfc7e6ff49a513b491e81000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b000000000000000000000000ec70dcb4a1efa46b8f2d97c310c9c4790ba5ffa800000000000000000000000000000000000000000000000005243d5e810723bd00000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005e00f493682e00000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000d28415565b00000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b000000000000000000000000ec70dcb4a1efa46b8f2d97c310c9c4790ba5ffa800000000000000000000000000000000000000000000000005243d5e810723bd00000000000000000000000000000000000000000000000000006339e5b80a6a00000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000003000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000ac0000000000000000000000000000000000000000000000000000000000000001500000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000540000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b00000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab100000000000000000000000000000000000000000000000000000000000001400000000000000000000000000000000000000000000000000000000000000500000000000000000000000000000000000000000000000000000000000000050000000000000000000000000000000000000000000000000000000000000004c000000000000000000000000000000000000000000000000005243d5e810723bd00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000500000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000001942616c616e636572563200000000000000000000000000000000000000000000000000000000000005243d5e810723bd0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000002a0000000000000000000000000ba12222222228d8ba445958a75a0704d566bf2c8000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000002200000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000e049b2de7d214070893c038299a57bac5acb8b8a340001000000000000000004be00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001409791d590788598535278552eecd4b211bfc790cb00000000000000000000049800000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b0000000000000000000000005979d7b546e38e414f7e9822514be443a480052900000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab10000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000015000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000004600000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000000000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab1000000000000000000000000ec70dcb4a1efa46b8f2d97c310c9c4790ba5ffa800000000000000000000000000000000000000000000000000000000000001400000000000000000000000000000000000000000000000000000000000000420000000000000000000000000000000000000000000000000000000000000042000000000000000000000000000000000000000000000000000000000000003e0ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000420000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000001942616c616e6365725632000000000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000000000000000000000000000000000000000000000006339e5b80a69000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000001c0000000000000000000000000ba12222222228d8ba445958a75a0704d566bf2c80000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000016000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000020ade4a71bb62bec25154cfc7e6ff49a513b491e8100000000000000000000049700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab1000000000000000000000000ec70dcb4a1efa46b8f2d97c310c9c4790ba5ffa80000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000030000000000000000000000001509706a6c66ca549ff0cb464de88231ddbe213b00000000000000000000000082af49447d8a07e3bd95bd0d56f35241523fbab1000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee0000000000000000000000000000000000000000000000000000000000000000869584cd000000000000000000000000100000000000000000000000000000000000001100000000000000000000000000000000db0a7093ced3022a78e356192f707a24000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000';


    function setUp() public {
        vm.createSelectFork(ARBITRUM_RPC_URL, ARBITRUM_FORK_BLOCK);
        TreasuryManager newTreasuryManger = new TreasuryManager(
            NotionalTreasuryAction(address(NOTIONAL)),
            WETH,
            TRADING_MODULE
        );
        vm.prank(NOTIONAL.owner());
        treasuryManager.upgradeTo(address(newTreasuryManger));
    }

    function test_reinvestVaultReward_SignatureMatchWithRewarderBot() public {
        vm.startPrank(treasuryManager.manager());
        treasuryManager.claimVaultRewardTokens(0x3Df035433cFACE65b6D68b77CC916085d020C8B8);
        (bool success,) = address(treasuryManager).call(reinvestData);
        require(success, "Reinvest call should succeed");
    }

}