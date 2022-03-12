import json
from brownie import Contract, TreasuryManager, nProxy, interface
from scripts.deployers.contract_deployer import ContractDeployer

TreasuryManagerConfig = {
    "goerli": {
        "vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "weth": "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1",
        "assetProxy": "0xB441EeD44B2B342972b173109DAFd2bdAd3260a5",
        "exchange": "0xB441EeD44B2B342972b173109DAFd2bdAd3260a5"
    }
}
SECONDS_IN_DAY = 86400

class TreasuryManagerDeployer:
    def __init__(self, network, deployer, config=None, persist=True) -> None:
        self.config = config
        if self.config == None:
            self.config = {}
        self.persist = persist
        self.network = network
        self.deployer = deployer
        self.staking = {}
        self._load()

    def _load(self):
        print("Loading TreasuryManager config")
        if self.persist:
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

        tokens = [
            TreasuryManagerConfig[self.network]["weth"],
            self.config["note"]
        ]

        # NOTE: Balancer requires token addresses to be sorted BAL#102
        tokens.sort()

        wethIndex = 0 if tokens[0] == TreasuryManagerConfig[self.network]["weth"] else 1
        noteIndex = 0 if tokens[0] == self.config["note"] else 1

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
            wethIndex,
            noteIndex
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
        