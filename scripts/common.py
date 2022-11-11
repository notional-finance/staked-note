import json
import eth_abi
import re
from brownie import Contract
from brownie.convert.datatypes import HexString

TokenType = {
    "UnderlyingToken": 0,
    "cToken": 1,
    "cETH": 2,
    "Ether": 3,
    "NonMintable": 4,
    "aToken": 5,
}

CurrencyId = {
    "ETH": 1,
    "DAI": 2,
    "USDC": 3,
    "WBTC": 4
}

CurrencySymbol = {
    1: "ETH",
    2: "DAI",
    3: "USDC",
    4: "WBTC"
}

DEX_ID = {
    'UNUSED': 0,
    'UNISWAP_V2': 1,
    'UNISWAP_V3': 2,
    'ZERO_EX': 3,
    'BALANCER_V2': 4,
    'CURVE': 5,
    'NOTIONAL_VAULT': 6
}

TRADE_TYPE = {
    'EXACT_IN_SINGLE': 0,
    'EXACT_OUT_SINGLE': 1,
    'EXACT_IN_BATCH': 2,
    'EXACT_OUT_BATCH': 3
}
    
def loadContractFromABI(name, address, path):
    with open(path, "r") as f:
        abi = json.load(f)
    return Contract.from_abi(name, address, abi)

def loadContractFromArtifact(name, address, path):
    with open(path, "r") as a:
        artifact = json.load(a)
    return Contract.from_abi(name, address, artifact["abi"])

def getDependencies(bytecode):
    deps = set()
    for marker in re.findall("_{1,}[^_]*_{1,}", bytecode):
        library = marker.strip("_")
        deps.add(library)
    result = list(deps)
    result.sort()
    return result

def encodeNTokenParams(config):
    return HexString("0x{}{}{}{}{}".format(
        hex(config[4])[2:],
        hex(config[3])[2:],
        hex(config[2])[2:],
        hex(config[1])[2:],
        hex(config[0])[2:]
    ), "bytes5")

def isProduction(network):
    return network == "mainnet" or network == "hardhat-fork"

def hasTransferFee(symbol):
    return symbol == "USDT"

def set_dex_flags(flags, **kwargs):
    binList = list(format(flags, "b").rjust(16, "0"))
    if "UNISWAP_V2" in kwargs:
        binList[1] = "1"
    if "UNISWAP_V3" in kwargs:
        binList[2] = "1"
    if "ZERO_EX" in kwargs:
        binList[3] = "1"
    if "BALANCER_V2" in kwargs:
        binList[4] = "1"
    if "CURVE" in kwargs:
        binList[5] = "1"
    if "NOTIONAL_VAULT" in kwargs:
        binList[6] = "1"
    return int("".join(reversed(binList)), 2)

def set_trade_type_flags(flags, **kwargs):
    binList = list(format(flags, "b").rjust(16, "0"))
    if "EXACT_IN_SINGLE" in kwargs:
        binList[0] = "1"
    if "EXACT_OUT_SINGLE" in kwargs:
        binList[1] = "1"
    if "EXACT_IN_BATCH" in kwargs:
        binList[2] = "1"
    if "EXACT_OUT_BATCH" in kwargs:
        binList[3] = "1"
    return int("".join(reversed(binList)), 2)

def get_univ3_single_data(fee):
    return eth_abi.encode_abi(['(uint24)'], [[fee]])
