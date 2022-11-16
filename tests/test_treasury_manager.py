
import pytest
import brownie
from brownie.network.state import Chain
from scripts.environment import create_environment, TestAccounts, Order
from scripts.common import DEX_ID, TRADE_TYPE, set_dex_flags, set_trade_type_flags, get_univ3_single_data

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
    assert pytest.approx(bptBefore, rel=1e-4) == 2644811198189584937030572
    env.treasuryManager.investWETHAndNOTE(0.1e18, 0, 0, {"from": testAccounts.testManager})
    bptAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert pytest.approx(bptAfter, rel=1e-4) == 2644925761215924412295058

def test_dex_trading():
    testAccounts = TestAccounts()
    env = create_environment()
    impl = env.deployTreasuryManager()
    env.treasuryManager.upgradeTo(impl, {"from": env.treasuryManager.owner()})
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer})
    env.treasuryManager.harvestCOMPFromNotional(
        ["0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5"], 
        {"from": testAccounts.testManager}
    )
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
    assert pytest.approx(env.weth.balanceOf(env.treasuryManager.address), rel=1e-4) == 14010883102666608721
    chain.undo()
    ret = env.treasuryManager.executeTrade.call(trade, DEX_ID["UNISWAP_V3"], {"from": testAccounts.testManager})
    assert ret[0] == amountSold
    assert ret[1] == amountBought
