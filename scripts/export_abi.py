import json

from brownie import TreasuryManager


def main():
    with open("abi/TreasuryManager.json", "w") as f:
        json.dump(TreasuryManager.abi, f, sort_keys=True, indent=4)
