import json
from brownie import Contract, stNOTE, nProxy, EmptyProxy

EnvironmentConfig = {
    "BalancerVault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    "WeightedPool2TokensFactory": "0xA5bf2ddF098bb0Ef6d120C98217dD6B141c74EE0",
    "NOTE": "0xCFEAead4947f0705A14ec42aC3D44129E1Ef3eD5",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "balancerPoolConfig": {
        "name": "Staked NOTE Weighted Pool",
        "symbol": "stNOTE-BPT",
        "tokens": [
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", # WETH
            "0xCFEAead4947f0705A14ec42aC3D44129E1Ef3eD5", # NOTE
        ],
        "weights": [ 0.2e18, 0.8e18 ],
        "swapFeePercentage": 0.005e18, # 0.5%
        "oracleEnable": True,
        "initBalances": [ 0.02e18, 80e8 ]
    },
    'stNOTEPoolAddress': None,
    'stNOTEPoolId': None,
    'stNOTEConfig': {
        'owner': '',
        'coolDownSeconds': 100
    }
}

class Environment:
    def __init__(self, config, deployer) -> None:
        self.config = config
        self.deployer = deployer
        self.balancerVault = self.loadBalancerVault(self.config["BalancerVault"])
        self.pool2TokensFactory = self.loadPool2TokensFactory(self.config["WeightedPool2TokensFactory"])
        self.note = self.loadNOTE(self.config["NOTE"])
        if self.config['stNOTEPoolAddress']:
            self.balancerPool = self.loadBalancerPool(self.config['stNOTEPoolAddress'])
            self.poolId = self.config['stNOTEPoolId']
            self.stNOTE = self.load_stNOTE(self.config['stNOTE'])
        else:
            self.stNOTEProxy = self.deployEmptyProxy()
            self.deployBalancerPool(self.config['balancerPoolConfig'], self.stNOTEProxy.address, self.deployer)
            self.stNOTE = self.upgrade_stNOTE()

        if self.config['stNOTE']:

    def load_stNOTE(self, address):
        return Contract.from_abi('stNOTE', address, stNOTE.abi)

    def loadBalancerPool(self, address):
        with open("./abi/balancer/pool.json", "r") as f:
            abi = json.load(f)
        return Contract.from_abi('BalancerPool', address, abi)

    def loadBalancerVault(self, address):
        with open("./abi/balancer/vault.json", "r") as f:
            abi = json.load(f)
        return Contract.from_abi('BalancerVault', address, abi)

    def loadPool2TokensFactory(self, address):
        with open("./abi/balancer/poolFactory.json", "r") as f:
            abi = json.load(f)
        return Contract.from_abi('Weighted Pool 2 Token Factory', address, abi)

    def deployEmptyProxy(self):
        # Deploys an empty proxy to get the stNOTE address
        emptyProxyImpl = EmptyProxy.deploy({"from": self.deployer})
        return nProxy.deploy(emptyProxyImpl.address, "", {"from": self.deployer})

    def upgrade_stNOTE(self):
        stNOTEImpl = stNOTE.deploy(
            self.balancerVault.address,
            self.poolId,
            self.note.address,
            {"from": self.deployer}
        )

        initializeCallData = stNOTEImpl.initialize.encode_calldata(
            self.config['stNOTEConfig']['owner'],
            self.config['stNOTEConfig']['coolDownSeconds']
        )

        self.stNOTEProxy.upgradeToAndCall(stNOTEImpl, initializeCallData, {'from': self.deployer})
        return self.load_stNOTE(self.stNOTEProxy.address)

    def deployBalancerPool(self, poolConfig, owner, deployer):
        # NOTE: owner is immutable, need to deploy the proxy first
        txn = self.pool2TokensFactory.create(
            poolConfig["name"],
            poolConfig["symbol"],
            poolConfig["tokens"],
            poolConfig["weights"],
            poolConfig["swapFeePercentage"],
            poolConfig["oracleEnable"],
            owner,
            {"from": deployer}
        )
        poolRegistered = txn.events["PoolRegistered"]
        self.balancerPool = self.loadBalancerPool(poolRegistered['poolAddress'])
        self.poolId = poolRegistered['poolId']

    def initBalancerPool(self, initializer):
        self.balancerVault.joinPool(
            self.poolId,
            initializer.address,
            self.stNOTE,
            eth_abi.encode_abi(
                [0, [self.config["balancerPoolConfig"]["initBalances"]]],
                ['uint256', 'uint256[]']
            )
        )

def main():
    deployer = accounts
    pass