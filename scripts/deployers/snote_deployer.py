import json
from brownie import Contract, EmptyProxy, nProxy, sNOTE, interface
from scripts.deployers.contract_deployer import ContractDeployer

SNoteConfig = {
    "goerli": {
        "vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "weth": "0xdFCeA9088c8A88A76FF74892C1457C17dfeef9C1",
        "owner": "0x2a956Fe94ff89D8992107c8eD4805c30ff1106ef",
        "coolDownSeconds": 100
    }
}

class SNoteDeployer:
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
        print("Loading sNOTE config")
        if self.persist:
            with open("v2.{}.json".format(self.network), "r") as f:
                self.config = json.load(f)
        if "staking" in self.config:
            self.staking = self.config["staking"]

    def _save(self):
        print("Saving sNOTE config")
        self.config["staking"] = self.staking
        if self.persist:
            with open("v2.{}.json".format(self.network), "w") as f:
                json.dump(self.config, f, sort_keys=True, indent=4)

    def _deployEmptyImpl(self):
        if "sNoteEmptyImpl" in self.staking:
            print("sNoteEmptyImpl deployed at {}".format(self.staking["sNoteEmptyImpl"]))
            return

        deployer = ContractDeployer(self.deployer)
        # Deploys an empty proxy to get the sNOTE address
        impl = deployer.deploy(EmptyProxy)
        self.staking["sNoteEmptyImpl"] = impl.address
        self._save()
        return impl
        
    def deployEmptyProxy(self):
        if "sNoteProxy" in self.staking:
            print("sNoteProxy deployed at {}".format(self.staking["sNoteProxy"]))
            return

        impl = self._deployEmptyImpl()
        deployer = ContractDeployer(self.deployer)
        proxy = deployer.deploy(nProxy, [impl.address, bytes()])
        self.staking["sNoteProxy"] = proxy.address
        self._save()

    def _deployImpl(self):
        if "sNoteImpl" in self.staking:
            print("sNoteImpl deployed at {}".format(self.staking["sNoteImpl"]))
            return Contract.from_abi("sNoteImpl", self.staking["sNoteImpl"], sNOTE.abi)

        tokens = [
            SNoteConfig[self.network]["weth"],
            self.config["note"]
        ]

        # NOTE: Balancer requires token addresses to be sorted BAL#102
        tokens.sort()

        wethIndex = 0 if tokens[0] == SNoteConfig[self.network]["weth"] else 1
        noteIndex = 0 if tokens[0] == self.config["note"] else 1

        deployer = ContractDeployer(self.deployer)
        impl = deployer.deploy(sNOTE, [
            SNoteConfig[self.network]["vault"],
            self.config["staking"]["pool"]["id"],
            wethIndex,
            noteIndex
        ])

        self.staking["sNoteImpl"] = impl.address
        self._save()
        return impl

    def upgradeSNote(self):
        impl = self._deployImpl()
        proxy = interface.UpgradeableProxy(self.staking["sNoteProxy"])

        if proxy.getImplementation() == impl.address:
            print("sNote does not need to be upgraded")
            return

        print("Upgrading sNote to {}".format(impl.address))

        # Upgrade only, no initialization
        if proxy.getImplementation() != self.staking["sNoteEmptyImpl"]:
            proxy.upgradeTo(impl.address, {"from": self.deployer})
            return

        # Upgrade and initialize
        initializeCallData = impl.initialize.encode_input(
            SNoteConfig[self.network]['owner'],
            SNoteConfig[self.network]['coolDownSeconds']
        )
        proxy.upgradeToAndCall(impl.address, initializeCallData, {"from": self.deployer})