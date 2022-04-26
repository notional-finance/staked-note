from brownie import sNOTE, interface, accounts, Contract

def main():
    deployer = accounts.load("MAINNET_DEPLOYER")
    oldImpl = sNOTE.at("0x64622768E55Dc2EC61A99C566094F4C45bbc294d")
    sNoteProxy = interface.UpgradeableProxy("0x38de42f4ba8a35056b33a746a6b45be9b1c3b9d2")
    owner = accounts.at("0x22341fb5d92d3d801144aa5a925f401a91418a05", force=True)
    sNoteImpl = sNOTE.deploy(
        oldImpl.BALANCER_VAULT(),
        oldImpl.NOTE_ETH_POOL_ID(),
        oldImpl.WETH_INDEX(),
        oldImpl.NOTE_INDEX(),
        "0x40ac67ea5bd1215d99244651cc71a03468bce6c0",
        "0x53144559c0d4a3304e2dd9dafbd685247429216d",
        "0x239e55F427D44C3cc793f49bFB507ebe76638a2b",
        {"from": deployer}
    )
    calldata = sNoteImpl.approveAndStakeAll.encode_input()
    sNoteProxy.upgradeToAndCall(sNoteImpl.address, calldata, {"from": owner})