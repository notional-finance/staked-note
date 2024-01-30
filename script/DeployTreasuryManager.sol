// SPDX-License-Identifier: GPL-3.0-only
pragma solidity =0.8.11;
pragma abicoder v2;

import {console2 as console} from "forge-std/console2.sol";
import {Script} from "forge-std/Script.sol";

import {TreasuryManager} from "../contracts/TreasuryManager.sol";
import {NotionalTreasuryAction} from "../interfaces/notional/NotionalTreasuryAction.sol";
import {ITradingModule} from "../interfaces/trading/ITradingModule.sol";
import {WETH9} from "../interfaces/WETH9.sol";

interface NotionalProxy {
    function owner() external returns (address);
}

contract DeployTreasuryManager is Script {
    mapping(uint256 => string) configFiles;

    function run() external {
        configFiles[1] = "v2.mainnet.json";
        configFiles[5] = "v2.goerli.json";
        configFiles[42161] = "v3.arbitrum-one.json";

        console.log("Deploying to chainid: ", block.chainid);

        string memory json = vm.readFile(configFiles[block.chainid]);

        NotionalProxy NOTIONAL = NotionalProxy(address(vm.parseJsonAddress(json, ".notional")));
        ITradingModule tradingModule = ITradingModule(vm.parseJsonAddress(json, ".tradingModule"));
        WETH9 WETH = WETH9(vm.parseJsonAddress(json, ".tokens.WETH.address"));
        TreasuryManager treasuryManager = TreasuryManager(address(vm.parseJsonAddress(json, ".staking.treasuryManager")));

        address owner = treasuryManager.owner();
        address manager = treasuryManager.manager();
        uint32 coolDownTimeInSeconds = treasuryManager.coolDownTimeInSeconds();

        vm.startBroadcast();

        TreasuryManager newTreasuryManger = new TreasuryManager(
            NotionalTreasuryAction(address(NOTIONAL)),
            WETH,
            tradingModule
        );

        treasuryManager.upgradeToAndCall(
            address(newTreasuryManger),
            abi.encodeWithSelector(TreasuryManager.initialize.selector, owner, manager, coolDownTimeInSeconds)
        );

        treasuryManager.initialize(
            owner,
            manager,
            coolDownTimeInSeconds
        );
        vm.stopBroadcast();
    }
}