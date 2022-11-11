
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

@pytest.mark.skip
def test_trading_DAI_good_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, {"from": testAccounts.DAIWhale})
    env.weth.approve(env.assetProxy.address, 2 ** 255, {"from": testAccounts.WETHWhale})
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 1000e18, env.weth.address, 1e18)
    DAIBefore = env.dai.balanceOf(env.treasuryManager.address)
    ETHBefore = env.weth.balanceOf(testAccounts.WETHWhale)
    env.exchangeV3.fillOrder(
        order.getParams(), 
        order.takerAssetAmount, 
        order.sign(env.exchangeV3, testAccounts.testManager),
        {"from": testAccounts.WETHWhale}
    )
    DAIAfter = env.dai.balanceOf(env.treasuryManager.address)
    ETHAfter = env.weth.balanceOf(testAccounts.WETHWhale)
    assert DAIBefore - DAIAfter == 1600e18
    assert ETHBefore - ETHAfter == 1e18

@pytest.mark.skip
def test_trading_DAI_very_good_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 900e18, env.weth.address, 1e18)
    DAIBefore = env.dai.balanceOf(env.treasuryManager.address)
    ETHBefore = env.weth.balanceOf(testAccounts.WETHWhale)
    env.exchangeV3.fillOrder(
        order.getParams(), 
        order.takerAssetAmount, 
        order.sign(env.exchangeV3, testAccounts.testManager),
        { "from": testAccounts.WETHWhale }
    )
    DAIAfter = env.dai.balanceOf(env.treasuryManager.address)
    ETHAfter = env.weth.balanceOf(testAccounts.WETHWhale)
    assert DAIBefore - DAIAfter == 1000e18
    assert ETHBefore - ETHAfter == 1e18

@pytest.mark.skip
def test_trading_DAI_bad_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 2000e18, env.weth.address, 1e18)
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

@pytest.mark.skip
def test_trading_DAI_bad_signature():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 1000e18, env.weth.address, 1e18)
    signature = order.sign(env.exchangeV3, testAccounts.testManager)
    newSig = signature[:5] + "2" + signature[6:]
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            newSig,
            { "from": testAccounts.WETHWhale }
        )

@pytest.mark.skip
def test_trading_DAI_bad_taker_token():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.usdc.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.USDCWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 1000e18, env.usdc.address, 2000e6)
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.USDCWhale }
        )

@pytest.mark.skip
def test_trading_DAI_bad_fee_recipient():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 1000e18, env.weth.address, 1e18)
    order.feeRecipientAddress = env.deployer.address
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

@pytest.mark.skip
def test_trading_DAI_bad_sender():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 1000e18, env.weth.address, 1e18)
    order.senderAddress = testAccounts.WETHWhale.address
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )


@pytest.mark.skip
def test_trading_DAI_bad_taker():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 1000e18, env.weth.address, 1e18)
    order.takerAddress = testAccounts.WETHWhale.address
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

@pytest.mark.skip
def test_trading_DAI_oracle_not_defined():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.bal.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setSlippageLimit(env.bal.address, 0.9e8, {"from": env.deployer})
    env.bal.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.BALWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.bal.address, 219e18, env.weth.address, 1e18)
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

@pytest.mark.skip
def test_trading_DAI_slippage_limit_not_defined():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.setSlippageLimit(env.dai.address, 0, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 1000e18, env.weth.address, 1e18)
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

@pytest.mark.skip
def test_trading_WETH():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.weth.address, 1e18, env.weth.address, 1e18)
    # WETH trading is not allowed
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

@pytest.mark.skip
def test_trading_WBTC_good_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.wbtc.transfer(env.treasuryManager.address, 1e8, { "from": testAccounts.WBTCWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.wbtc.address, 1e8, env.weth.address, 15e18)
    WBTCBefore = env.wbtc.balanceOf(env.treasuryManager.address)
    ETHBefore = env.weth.balanceOf(testAccounts.WETHWhale)
    env.exchangeV3.fillOrder(
        order.getParams(), 
        order.takerAssetAmount, 
        order.sign(env.exchangeV3, testAccounts.testManager),
        { "from": testAccounts.WETHWhale }
    )
    WBTCAfter = env.wbtc.balanceOf(env.treasuryManager.address)
    ETHAfter = env.weth.balanceOf(testAccounts.WETHWhale)
    assert WBTCBefore - WBTCAfter == 1e8
    assert ETHBefore - ETHAfter == 12e18

@pytest.mark.skip
def test_trading_WBTC_bad_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.wbtc.transfer(env.treasuryManager.address, 1e8, { "from": testAccounts.WBTCWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.wbtc.address, 1e8, env.weth.address, 8e18)
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

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

@pytest.mark.skip
def test_trading_DAI_non_zero_fees():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 4000e18, env.weth.address, 1e18)
    order.makerFee = 2000e18
    order.takerFee = 0.5e18
    with brownie.reverts():
        env.exchangeV3.fillOrder.call(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

@pytest.mark.skip
def test_cancel_order_success():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 4000e18, env.weth.address, 1e18)
    statusBefore = env.exchangeV3.getOrderInfo(order.getParams())[0]
    assert statusBefore == 3 # FILLABLE
    env.treasuryManager.cancelOrder(order.getParams(), {"from": testAccounts.testManager})
    statusAfter = env.exchangeV3.getOrderInfo(order.getParams())[0]
    assert statusAfter == 6 # CANCELLED

@pytest.mark.skip
def test_cancel_order_non_manager():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.assetProxy.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 4000e18, env.weth.address, 1e18)
    statusBefore = env.exchangeV3.getOrderInfo(order.getParams())[0]
    assert statusBefore == 3 # FILLABLE
    with brownie.reverts():
        env.treasuryManager.cancelOrder.call(order.getParams(), {"from": env.deployer})
    statusAfter = env.exchangeV3.getOrderInfo(order.getParams())[0]
    assert statusAfter == 3 # FILLABLE

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
    assert pytest.approx(bptBefore, rel=1e-4) == 2681104964191060915650071
    env.treasuryManager.investWETHAndNOTE(0.1e18, 0, 0, {"from": testAccounts.testManager})
    bptAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert pytest.approx(bptAfter, rel=1e-4) == 2681210603455045401060799

def test_dex_trading():
    testAccounts = TestAccounts()
    env = create_environment()
    impl = env.deployTreasuryManager()
    env.treasuryManager.upgradeTo(impl, {"from": env.treasuryManager.owner()})
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
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
    assert env.weth.balanceOf(env.treasuryManager.address) == 0
    env.treasuryManager.executeTrade(trade, DEX_ID["UNISWAP_V3"], {"from": testAccounts.testManager})
    assert pytest.approx(env.weth.balanceOf(env.treasuryManager.address), rel=1e-4) == 3240870833743493949