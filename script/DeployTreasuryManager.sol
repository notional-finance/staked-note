// SPDX-License-Identifier: GPL-3.0-only
pragma solidity =0.8.11;
pragma abicoder v2;

import {Script} from "forge-std/Script.sol";

import {TreasuryManager} from "../contracts/TreasuryManager.sol";
import {NotionalTreasuryAction} from "../interfaces/notional/NotionalTreasuryAction.sol";
import {ITradingModule} from "../interfaces/trading/ITradingModule.sol";
import {WETH9} from "../interfaces/WETH9.sol";

interface NotionalProxy {
    function owner() external returns (address);
}

contract DeployTreasuryAction is Script {
    mapping(uint256 => string) configFiles;

    function run() external {
        configFiles[1] = "v2.mainnet.json";
        configFiles[5] = "v2.goerli.json";

        uint256 chainId;
        assembly {
            chainId := chainid()
        }

        string memory json = vm.readFile(configFiles[chainId]);

        NotionalProxy NOTIONAL = NotionalProxy(address(vm.parseJsonAddress(json, ".notional")));
        ITradingModule tradingModule = ITradingModule(vm.parseJsonAddress(json, ".tradingModule"));
        WETH9 WETH = WETH9(vm.parseJsonAddress(json, ".tokens.WETH.address"));
        TreasuryManager treasuryManager = TreasuryManager(address(vm.parseJsonAddress(json, ".staking.treasuryManager")));

        vm.startBroadcast(NOTIONAL.owner());

        TreasuryManager newTreasuryManger = new TreasuryManager(
            NotionalTreasuryAction(address(NOTIONAL)),
            WETH,
            tradingModule
        );

        treasuryManager.upgradeTo(address(newTreasuryManger));
        vm.stopBroadcast();
    }
}

