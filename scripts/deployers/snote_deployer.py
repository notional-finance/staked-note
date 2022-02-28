import json
from brownie import Contract, EmptyProxy, nProxy
from scripts.deployers.contract_deployer import ContractDeployer

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

    def _deployEmptyProxyImpl(self):
        if "sNoteEmptyProxyImpl" in self.staking:
            print("sNoteEmptyProxyImpl deployed at {}".format(self.staking["sNoteEmptyProxyImpl"]))
            return

        deployer = ContractDeployer(self.deployer)
        # Deploys an empty proxy to get the sNOTE address
        impl = deployer.deploy(EmptyProxy)
        self.staking["sNoteEmptyProxyImpl"] = impl.address
        self._save()
        return impl
        

    def deployEmptyProxy(self):
        if "sNoteProxy" in self.staking:
            print("sNoteProxy deployed at {}".format(self.staking["sNoteProxy"]))
            return

        impl = self._deployEmptyProxyImpl()
        deployer = ContractDeployer(self.deployer)
        proxy = deployer.deploy(nProxy, [impl.address, bytes()])
        self.staking["sNoteProxy"] = proxy.address
        self._save()

    def deploy():
        pass