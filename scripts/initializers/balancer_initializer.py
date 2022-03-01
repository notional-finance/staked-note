import json
import eth_abi
from brownie import Contract, Wei, sNOTE

from scripts.deployers.snote_deployer import SNoteConfig

ETH_ADDRESS = "0x0000000000000000000000000000000000000000"
BalancerConfig = {
    "goerli": {
        "vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "weth": "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1",
        "initBalances": [ Wei(1e8), Wei(0.2e18) ]
    }
}

class BalancerInitializer:
    def __init__(self, network, deployer, config=None, persist=True) -> None:
        self.config = config
        if self.config == None:
            self.config = {}
        self.persist = persist
        self.network = network
        self.deployer = deployer
        self._load()

    def _load(self):
        if self.persist:
            with open("v2.{}.json".format(self.network), "r") as f:
                self.config = json.load(f)
        self.vault = self._loadVault(BalancerConfig[self.network]["vault"])
        self.pool = self._loadPool(self.config["staking"]["pool"]["address"])
        self.note = self._loadNote(self.config["note"])
        self.sNote = self._loadSNote(self.config["staking"]["sNoteProxy"])
        self.weth = self._loadWETH()

    def _loadPool(self, address):
        with open("./abi/balancer/pool.json", "r") as f:
            abi = json.load(f)
        return Contract.from_abi('BalancerPool', address, abi)

    def _loadSNote(self, address):
        return Contract.from_abi('sNOTE', address, sNOTE.abi)
        
    def _loadWETH(self):
        with open("./abi/ERC20.json", "r") as f:
            abi = json.load(f)
        return Contract.from_abi("WETH", SNoteConfig[self.network]["weth"], abi)

    def _loadNote(self, address):
        with open("./abi/notional/note.json", "r") as f:
            abi = json.load(f)
        return Contract.from_abi('NOTE', address, abi)

    def _loadVault(self, address):
        with open("./abi/balancer/vault.json", "r") as f:
            abi = json.load(f)
        return Contract.from_abi('BalancerVault', address, abi)

    def initPool(self):
        bptBalance = self.pool.balanceOf(self.sNote)
        print("BPT amount {}".format(bptBalance))

        if bptBalance > 0:
            print("Balancer pool already initialized")
            return

        self.note.approve(self.vault.address, 2**256 - 1, {"from": self.deployer})
        self.weth.approve(self.vault.address, 2**256 - 1, {"from": self.deployer})
        userData = eth_abi.encode_abi(
            ['uint256', 'uint256[]'],
            [0, BalancerConfig[self.network]["initBalances"]]
        )

        self.vault.joinPool(
            self.config["staking"]["pool"]["id"],
            self.deployer.address,
            self.sNote.address,
            (
                [self.note.address, ETH_ADDRESS],
                BalancerConfig[self.network]["initBalances"],
                userData,
                False
            ),
            {
                "from": self.deployer,
                "value": BalancerConfig[self.network]["initBalances"][1]
            }
        )
