import json
from brownie import TreasuryManager
from scripts.deployers.contract_deployer import ContractDeployer

class TreasuryManagerDeployer:
    def __init__(self, network, deployer, config=None, persist=True) -> None:
        self.config = config
        if self.config == None:
            self.config = {}
        self.persist = persist
        self.network = network
        self.deployer = deployer
        self._load()

    def _load(self):
        print("Loading TreasuryManager config")
        if self.persist:
            with open("v2.{}.json".format(self.network), "r") as f:
                self.config = json.load(f)

    def _save(self):
        print("Saving TreasuryManager config")
        if self.persist:
            with open("v2.{}.json".format(self.network), "w") as f:
                json.dump(self.config, f, sort_keys=True, indent=4)

    def deploy(self):
        deployer = ContractDeployer(self.deployer)
        # Deploy NOTE implementation contract
        #contract = deployer.deploy(TreasuryManager, [
        #    self.config["notional"],
        #    self.config["tokens"]["WETH"]["address"],
        #    self.config["staking"]["vault"],
        #    _noteETHPoolId,
        #    self.config["note"],
        #    self.config["staking"]["snote"],
        #    _assetProxy,
        #    _exchange
        #], "TreasuryManagerImpl", True)
