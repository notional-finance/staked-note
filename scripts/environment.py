import json
import eth_abi
from brownie import accounts, Contract, sNOTE, nProxy, EmptyProxy
from brownie.convert.datatypes import Wei

ETH_ADDRESS = "0x0000000000000000000000000000000000000000"

EnvironmentConfig = {
    "BalancerVault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    "WeightedPool2TokensFactory": "0xA5bf2ddF098bb0Ef6d120C98217dD6B141c74EE0",
    "NOTE": "0xCFEAead4947f0705A14ec42aC3D44129E1Ef3eD5",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "balancerPoolConfig": {
        "name": "Staked NOTE Weighted Pool",
        "symbol": "sNOTE-BPT",
        "tokens": [
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", # WETH
            "0xCFEAead4947f0705A14ec42aC3D44129E1Ef3eD5", # NOTE
        ],
        "weights": [ 0.2e18, 0.8e18 ],
        "swapFeePercentage": 0.005e18, # 0.5%
        "oracleEnable": True,
        "initBalances": [ Wei(0.002e18), Wei(0.01e8) ]
    },
    'sNOTEPoolAddress': None,
    'sNOTEPoolId': None,
    'sNOTEConfig': {
        'owner': '0x22341fB5D92D3d801144aA5A925F401A91418A05',
        'coolDownSeconds': 100
    }
}

class TestAccounts:
    def __init__(self) -> None:
        self.DAIWhale = accounts.at("0x6dfaf865a93d3b0b5cfd1b4db192d1505676645b", force=True) # A good source of DAI
        self.cDAIWhale = accounts.at("0x33b890d6574172e93e58528cd99123a88c0756e9", force=True) # A good source of cDAI
        self.ETHWhale = accounts.at("0x7D24796f7dDB17d73e8B1d0A3bbD103FBA2cb2FE", force=True) # A good source of ETH
        self.cETHWhale = accounts.at("0x1a1cd9c606727a7400bb2da6e4d5c70db5b4cade", force=True) # A good source of cETH
        self.NOTEWhale = accounts.at("0x22341fB5D92D3d801144aA5A925F401A91418A05", force=True)
        self.deployer = accounts.at("0x2a956Fe94ff89D8992107c8eD4805c30ff1106ef", force=True)

class Environment:
    def __init__(self, config, deployer) -> None:
        self.config = config
        self.deployer = deployer
        self.balancerVault = self.loadBalancerVault(self.config["BalancerVault"])
        self.pool2TokensFactory = self.loadPool2TokensFactory(self.config["WeightedPool2TokensFactory"])
        self.note = self.loadNOTE(self.config["NOTE"])
        if self.config['sNOTEPoolAddress']:
            self.balancerPool = self.loadBalancerPool(self.config['sNOTEPoolAddress'])
            self.poolId = self.config['sNOTEPoolId']
            self.sNOTE = self.load_sNOTE(self.config['sNOTE'])
        else:
            self.sNOTEProxy = self.deployEmptyProxy()
            self.deployBalancerPool(self.config['balancerPoolConfig'], self.sNOTEProxy.address, self.deployer)
            self.sNOTE = self.upgrade_sNOTE()
            self.initBalancerPool(self.deployer)

    def loadNOTE(self, address):
        with open("./abi/notional/note.json", "r") as f:
            abi = json.load(f)
        return Contract.from_abi('NOTE', address, abi)

    def load_sNOTE(self, address):
        return Contract.from_abi('sNOTE', address, sNOTE.abi)

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
        # Deploys an empty proxy to get the sNOTE address
        emptyProxyImpl = EmptyProxy.deploy({"from": self.deployer})
        proxy = nProxy.deploy(emptyProxyImpl.address, bytes(), {"from": self.deployer})
        return Contract.from_abi("Proxy", proxy.address, EmptyProxy.abi)

    def upgrade_sNOTE(self):
        sNOTEImpl = sNOTE.deploy(
            self.balancerVault.address,
            self.poolId,
            self.note.address,
            {"from": self.deployer}
        )

        initializeCallData = sNOTEImpl.initialize.encode_input(
            self.config['sNOTEConfig']['owner'],
            self.config['sNOTEConfig']['coolDownSeconds']
        )

        self.sNOTEProxy.upgradeToAndCall(sNOTEImpl, initializeCallData, {'from': self.deployer})
        return self.load_sNOTE(self.sNOTEProxy.address)

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
        self.note.approve(self.balancerVault.address, 2**256 - 1, {"from": initializer})
        userData = eth_abi.encode_abi(
            ['uint256', 'uint256[]'],
            [0, self.config["balancerPoolConfig"]["initBalances"]]
        )

        self.balancerVault.joinPool(
            self.poolId,
            initializer.address,
            self.sNOTE,
            (
                [ETH_ADDRESS, self.note.address],
                self.config['balancerPoolConfig']["initBalances"],
                userData,
                False
            ),
            {
                "from": initializer,
                "value": self.config["balancerPoolConfig"]["initBalances"][0]
            }
        )

def create_environment():
    testAccounts = TestAccounts()
    return Environment(EnvironmentConfig, testAccounts.NOTEWhale)

def main():
    testAccounts = TestAccounts()
    env = Environment(EnvironmentConfig, testAccounts.NOTEWhale)