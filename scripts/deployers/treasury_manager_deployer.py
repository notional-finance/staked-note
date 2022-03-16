import json
from brownie import Contract, TreasuryManager, nProxy, interface
from scripts.deployers.contract_deployer import ContractDeployer

TreasuryManagerConfig = {
    "goerli": {
        "vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "weth": "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1",
        "assetProxy": "0xB441EeD44B2B342972b173109DAFd2bdAd3260a5",
        "exchange": "0xB441EeD44B2B342972b173109DAFd2bdAd3260a5",
        "wethIndex": 1,
        "noteIndex": 0
    },
    "kovan": {
        "vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "weth": "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1",
        "assetProxy": "0xf1ec01d6236d3cd881a0bf0130ea25fe4234003e",
        "exchange": "0x4eacd0af335451709e1e7b570b8ea68edec8bc97",
        "wethIndex": 1,
        "noteIndex": 0
    },
    "mainnet": {
        "vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "assetProxy": "0x95E6F48254609A6ee006F7D493c8e5fB97094ceF",
        "exchange": "0x61935cbdd02287b511119ddb11aeb42f1593b7ef",
        "wethIndex": 0,
        "noteIndex": 1        
    }
}
SECONDS_IN_DAY = 86400

class TreasuryManagerDeployer:
    def __init__(self, network, deployer, config=None, persist=True) -> None:
        self.config = config
        self.persist = persist
        self.network = network
        if self.network == "hardhat-fork":
            self.network = "mainnet"
            self.persist = False
        self.deployer = deployer
        self.staking = {}
        self._load()

    def _load(self):
        print("Loading TreasuryManager config")
        if self.config == None:
            with open("v2.{}.json".format(self.network), "r") as f:
                self.config = json.load(f)
        self.staking = self.config["staking"]

    def _save(self):
        print("Saving TreasuryManager config")
        self.config["staking"] = self.staking
        if self.persist:
            with open("v2.{}.json".format(self.network), "w") as f:
                json.dump(self.config, f, sort_keys=True, indent=4)

    def _deployTreasuryManagerImpl(self):
        if "treasuryManagerImpl" in self.staking:
            return Contract.from_abi("TreasuryManagerImpl", self.staking["treasuryManagerImpl"], TreasuryManager.abi)

        deployer = ContractDeployer(self.deployer)
        impl = deployer.deploy(TreasuryManager, [
            self.config["notional"],
            TreasuryManagerConfig[self.network]["weth"],
            TreasuryManagerConfig[self.network]["vault"],
            self.config["staking"]["pool"]["id"],
            self.config["note"],
            self.config["staking"]["sNoteProxy"],
            TreasuryManagerConfig[self.network]["assetProxy"],
            TreasuryManagerConfig[self.network]["exchange"],
            TreasuryManagerConfig[self.network]["wethIndex"],
            TreasuryManagerConfig[self.network]["noteIndex"]
        ], "TreasuryManagerImpl")
        self.staking["treasuryManagerImpl"] = impl.address
        self._save()
        return impl

    def deploy(self):
        impl = self._deployTreasuryManagerImpl()

        if "treasuryManager" in self.staking:
            print("treasuryManager deployed at {}".format(self.staking["treasuryManager"]))

            proxy = interface.UpgradeableProxy(self.staking["treasuryManager"])
            current = proxy.getImplementation()

            if current != impl.address:
                print("Upgrading treasury manager from {} to {}".format(current, impl.address))
                proxy.upgradeTo(impl.address, {"from": self.deployer})
            return

        initData = impl.initialize.encode_input(self.deployer, self.deployer, SECONDS_IN_DAY)
        deployer = ContractDeployer(self.deployer)
        proxy = deployer.deploy(nProxy, [impl.address, initData])
        self.staking["treasuryManager"] = proxy.address
        self._save()    
        