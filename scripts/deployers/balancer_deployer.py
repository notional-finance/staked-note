import json
from brownie import Contract

BalancerConfig = {
    "goerli": {
        "factory": "0xA5bf2ddF098bb0Ef6d120C98217dD6B141c74EE0"
    }
}

class BalancerDeployer:
    def __init__(self, network, deployer, config=None, persist=True) -> None:
        self.config = config
        if self.config == None:
            self.config = {}
        self.persist = persist
        self.network = network
        self.deployer = deployer
        self.staking = {}
        self._load()
        self.pool2TokensFactory = self._loadPool2TokensFactory()

    def _load(self):
        print("Loading balancer config")
        if self.persist:
            with open("v2.{}.json".format(self.network), "r") as f:
                self.config = json.load(f)
        if "staking" in self.config:
            self.staking = self.config["staking"]

    def _save(self):
        print("Saving balancer config")
        self.config["staking"] = self.staking
        if self.persist:
            with open("v2.{}.json".format(self.network), "w") as f:
                json.dump(self.config, f, sort_keys=True, indent=4)

    def _loadPool2TokensFactory(self):
        with open("./abi/balancer/poolFactory.json", "r") as f:
            abi = json.load(f)
        return Contract.from_abi(
            'Weighted Pool 2 Token Factory',
            BalancerConfig[self.network]["factory"], 
            abi
        )

    def deployNotePool(self):
        # NOTE: owner is immutable, need to deploy the proxy first
        txn = self.pool2TokensFactory.create(
            BalancerConfig[self.network]["name"],
            BalancerConfig[self.network]["symbol"],
            BalancerConfig[self.network]["tokens"],
            BalancerConfig[self.network]["weights"],
            BalancerConfig[self.network]["swapFeePercentage"],
            BalancerConfig[self.network]["oracleEnable"],
            owner,
            {"from": self.deployer}
        )
        poolRegistered = txn.events["PoolRegistered"]
        self.balancerPool = self.loadBalancerPool(poolRegistered['poolAddress'])
        self.poolId = poolRegistered['poolId']