
import pytest
import brownie
import eth_abi
import json
from brownie import Contract, ZERO_ADDRESS, Wei
from brownie.network.state import Chain
from scripts.environment import create_environment, TestAccounts
from scripts.common import (
    DEX_ID, 
    TRADE_TYPE, 
    set_dex_flags, 
    set_trade_type_flags, 
    get_univ3_single_data, 
    get_univ3_batch_data
)

chain = Chain()
@pytest.fixture(autouse=True)
def run_around_tests():
    chain.snapshot()
    yield
    chain.revert()

def test_set_price_oracle_non_owner():
    testAccounts = TestAccounts()
    env = create_environment()
    with brownie.reverts():
        env.treasuryManager.setPriceOracle.call(
            env.dai.address, 
            '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', 
            {"from": testAccounts.WETHWhale}
        )

def test_set_slippage_limit_non_owner():
    testAccounts = TestAccounts()
    env = create_environment()
    with brownie.reverts():
        env.treasuryManager.setSlippageLimit.call(env.dai.address, 0.9e8, {"from": testAccounts.WETHWhale})

def test_set_note_purchase_limit_non_owner():
    testAccounts = TestAccounts()
    env = create_environment()
    with brownie.reverts():
        env.treasuryManager.setNOTEPurchaseLimit.call(0.2e8, {"from": testAccounts.WETHWhale})

def test_invest_eth():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.weth.transfer(env.treasuryManager.address, 1e18, {"from": testAccounts.WETHWhale})
    env.weth.approve(env.balancerVault.address, 2 ** 255, {"from": testAccounts.WETHWhale})
    env.note.approve(env.balancerVault.address, 2 ** 255, {"from": testAccounts.WETHWhale})
    # Initialize price oracle
    env.buyNOTE(1e8, testAccounts.WETHWhale)
    env.sellNOTE(1e8, testAccounts.WETHWhale)
    chain.sleep(3600)
    chain.mine()
    bptBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert pytest.approx(bptBefore, rel=1e-2) == 2793897870994194541513251
    env.treasuryManager.investWETHAndNOTE(0.1e18, 0, 0, {"from": testAccounts.testManager})
    bptAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert pytest.approx(bptAfter, rel=1e-2) == 2794037790183842568520045

def test_dex_trading():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer})
    env.tradingModule.setTokenPermissions(
        env.treasuryManager.address, 
        env.comp.address, 
        [
            True, 
            set_dex_flags(0, UNISWAP_V2=True, UNISWAP_V3=True), 
            set_trade_type_flags(0, EXACT_IN_SINGLE=True, EXACT_IN_BATCH=True)
        ], 
        {"from": env.notional.owner()})
    trade = [
        TRADE_TYPE["EXACT_IN_SINGLE"], # Exact in
        env.comp.address,
        env.weth.address,
        env.comp.balanceOf(env.treasuryManager.address),
        0,
        chain.time() + 20000,
        get_univ3_single_data(3000)
    ]
    amountSold = env.comp.balanceOf(env.treasuryManager.address)
    assert env.weth.balanceOf(env.treasuryManager.address) == 0
    env.treasuryManager.executeTrade(trade, DEX_ID["UNISWAP_V3"], {"from": testAccounts.testManager})
    amountBought = env.weth.balanceOf(env.treasuryManager.address)
    assert pytest.approx(env.weth.balanceOf(env.treasuryManager.address), rel=1e-2) == 19557205283290795929
    chain.undo()
    ret = env.treasuryManager.executeTrade.call(trade, DEX_ID["UNISWAP_V3"], {"from": testAccounts.testManager})
    assert ret[0] == amountSold
    assert ret[1] == amountBought

def get_metastable_amounts(poolContext, amount):
    primaryBalance = poolContext["basePool"]["primaryBalance"]
    secondaryBalance = poolContext["basePool"]["secondaryBalance"]
    primaryRatio = primaryBalance / (primaryBalance + secondaryBalance)
    primaryAmount = amount * primaryRatio
    secondaryAmount = amount - primaryAmount
    return (Wei(primaryAmount), Wei(secondaryAmount))

def test_reinvestment_events():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer})
    with open("abi/vaults/balancer/MetaStable2TokenAuraVault.json", "r") as f:
        vaultABI = json.load(f);
    vault = Contract.from_abi("MetaStable2TokenAuraVault", "0xF049B944eC83aBb50020774D48a8cf40790996e6", vaultABI)
    data = vault.setStrategyVaultSettings.encode_input(
        [20000000000000000000,1000000,1000000,1000000,1500,20,200,9975]
    )
    vault.upgradeToAndCall("0xE92209d60384d91832fAc0b928DB2C2eA2437AfD", data, {"from": env.notional.owner()})
    vault.grantRole(vault.getRoles().dict()["rewardReinvestment"], env.treasuryManager.address, {"from": env.notional.owner()})
    env.treasuryManager.claimVaultRewardTokens(vault.address, {"from": testAccounts.testManager})

    rewardAmount = env.bal.balanceOf(vault.address)
    tradeParams = "(uint16,uint8,uint256,bool,bytes)"
    singleSidedRewardTradeParams = "(address,address,uint256,{})".format(tradeParams)
    proportional2TokenRewardTradeParams = "({},{})".format(singleSidedRewardTradeParams, singleSidedRewardTradeParams)
    (primaryAmount, secondaryAmount) = get_metastable_amounts(vault.getStrategyContext()["poolContext"], rewardAmount)
    rewardParams = [eth_abi.encode_abi(
        [proportional2TokenRewardTradeParams],
        [[
            [
                env.bal.address,
                ZERO_ADDRESS,
                primaryAmount,
                [
                    DEX_ID["UNISWAP_V3"],
                    TRADE_TYPE["EXACT_IN_SINGLE"],
                    0,
                    False,
                    get_univ3_single_data(3000)
                ]
            ],
            [
                env.bal.address,
                env.wstETH.address,
                secondaryAmount,
                [
                    DEX_ID["UNISWAP_V3"],
                    TRADE_TYPE["EXACT_IN_BATCH"],
                    Wei(0.05e18), # static slippage
                    False,
                    get_univ3_batch_data([
                        env.bal.address, 3000, env.weth.address, 500, env.wstETH.address
                    ])
                ]
            ]
        ]]
    ), 0]

    ret = env.treasuryManager.reinvestVaultReward.call(vault.address, rewardParams, {"from": testAccounts.testManager})
    tx = env.treasuryManager.reinvestVaultReward(vault.address, rewardParams, {"from": testAccounts.testManager})
    event = tx.events["VaultRewardReinvested"]
    assert event["vault"] == "0xF049B944eC83aBb50020774D48a8cf40790996e6"
    assert event["rewardToken"] == ret[0]
    assert event["primaryAmount"] == ret[1]
    assert event["secondaryAmount"] == ret[2]
    assert event["poolClaimAmount"] == ret[3]
    assert event["strategyTokenAmount"] == ret[4]