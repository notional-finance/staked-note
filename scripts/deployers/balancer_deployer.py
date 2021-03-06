import json
from brownie import Contract

BalancerConfig = {
    "goerli": {
        "factory": "0xA5bf2ddF098bb0Ef6d120C98217dD6B141c74EE0",
        "weth": "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1",
        "name": "Staked NOTE Weighted Pool",
        "symbol": "sNOTE-BPT",
        "weights": [ 0.8e18, 0.2e18 ],
        "swapFeePercentage": 0.005e18, # 0.5%
        "oracleEnable": True
    },
    "kovan": {
        "factory": "0xA5bf2ddF098bb0Ef6d120C98217dD6B141c74EE0",
        "weth": "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1",
        "name": "Staked NOTE Weighted Pool",
        "symbol": "sNOTE-BPT",
        "weights": [ 0.8e18, 0.2e18 ],
        "swapFeePercentage": 0.005e18, # 0.5%
        "oracleEnable": True        
    },
    "mainnet": {
        "factory": "0xA5bf2ddF098bb0Ef6d120C98217dD6B141c74EE0",
        "weth": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "name": "Staked NOTE Weighted Pool",
        "symbol": "sNOTE-BPT",
        "weights": [ 0.2e18, 0.8e18 ],
        "swapFeePercentage": 0.005e18, # 0.5%
        "oracleEnable": True        
    }
}

class BalancerDeployer:
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
        self.pool2TokensFactory = self._loadPool2TokensFactory()

    def _load(self):
        print("Loading balancer config")
        if self.config == None:
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
        if "pool" in self.staking:
            print("pool address={} id={}".format(self.staking["pool"]["address"], self.staking["pool"]["id"]))
            return

        tokens = [
            BalancerConfig[self.network]["weth"],
            self.config["note"]
        ]

        # NOTE: Balancer requires token addresses to be sorted BAL#102
        tokens.sort()

        # NOTE: owner is immutable, need to deploy the proxy first
        txn = self.pool2TokensFactory.create(
            BalancerConfig[self.network]["name"],
            BalancerConfig[self.network]["symbol"],
            tokens,
            BalancerConfig[self.network]["weights"],
            BalancerConfig[self.network]["swapFeePercentage"],
            BalancerConfig[self.network]["oracleEnable"],
            self.config["staking"]["sNoteProxy"],
            {"from": self.deployer}
        )
        poolRegistered = txn.events["PoolRegistered"]
        self.staking["pool"] = {
            "address": poolRegistered['poolAddress'],
            "id": str(poolRegistered['poolId'])
        }
        print("Pool created address={} id={}".format(poolRegistered['poolAddress'], str(poolRegistered['poolId'])))
        self._save()
