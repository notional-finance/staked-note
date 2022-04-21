
import pytest
import brownie
from brownie.network.state import Chain
from scripts.environment import create_environment, TestAccounts, Order

chain = Chain()
@pytest.fixture(autouse=True)
def run_around_tests():
    chain.snapshot()
    yield
    chain.revert()

def test_trading_DAI_good_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 3000e18, env.weth.address, 1e18)
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
    assert DAIBefore - DAIAfter == 3000e18
    assert ETHBefore - ETHAfter == 1e18

def test_trading_DAI_very_good_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 2000e18, env.weth.address, 1e18)
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
    assert DAIBefore - DAIAfter == 2000e18
    assert ETHBefore - ETHAfter == 1e18

def test_trading_DAI_bad_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 5000e18, env.weth.address, 1e18)
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

def test_trading_DAI_bad_signature():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 2000e18, env.weth.address, 1e18)
    signature = order.sign(env.exchangeV3, testAccounts.testManager)
    newSig = signature[:5] + "2" + signature[6:]
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            newSig,
            { "from": testAccounts.WETHWhale }
        )

def test_trading_DAI_bad_taker_token():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.usdc.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.USDCWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 2000e18, env.usdc.address, 2000e6)
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.USDCWhale }
        )

def test_trading_DAI_bad_fee_recipient():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 2000e18, env.weth.address, 1e18)
    order.feeRecipientAddress = env.deployer.address
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

def test_trading_DAI_bad_sender():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 4000e18, env.weth.address, 1e18)
    order.senderAddress = testAccounts.WETHWhale.address
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )


def test_trading_DAI_bad_taker():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 4000e18, env.weth.address, 1e18)
    order.takerAddress = testAccounts.WETHWhale.address
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

def test_trading_DAI_oracle_not_defined():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 2000e18, env.weth.address, 1e18)
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

def test_trading_DAI_slippage_limit_not_defined():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 2000e18, env.weth.address, 1e18)
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

def test_trading_WETH():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.weth.address, 1e18, env.weth.address, 1e18)
    # WETH trading is not allowed
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

def test_trading_WBTC_good_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.wbtc.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.wbtc.address, '0x10aae34011c256a9e63ab5ac50154c2539c0f51d', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.wbtc.address, 0.9e8, {"from": env.deployer})
    env.wbtc.transfer(env.treasuryManager.address, 1e8, { "from": testAccounts.WBTCWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.wbtc.address, 1e8, env.weth.address, 12.3e18)
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
    assert ETHBefore - ETHAfter == 12.3e18


def test_trading_WBTC_bad_price():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.wbtc.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.wbtc.address, '0x10aae34011c256a9e63ab5ac50154c2539c0f51d', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.wbtc.address, 0.9e8, {"from": env.deployer})
    env.wbtc.transfer(env.treasuryManager.address, 1e8, { "from": testAccounts.WBTCWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.wbtc.address, 1.3e8, env.weth.address, 12.3e18)
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

def test_set_price_oracle_non_owner():
    testAccounts = TestAccounts()
    env = create_environment()
    with brownie.reverts():
        env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": testAccounts.WETHWhale})

def test_set_slippage_limit_non_owner():
    testAccounts = TestAccounts()
    env = create_environment()
    with brownie.reverts():
        env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": testAccounts.WETHWhale})

def test_set_note_purchase_limit_non_owner():
    testAccounts = TestAccounts()
    env = create_environment()
    with brownie.reverts():
        env.treasuryManager.setNOTEPurchaseLimit(0.2e8, {"from": testAccounts.WETHWhale})

def test_trading_DAI_non_zero_fees():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 4000e18, env.weth.address, 1e18)
    order.makerFee = 2000e18
    order.takerFee = 0.5e18
    with brownie.reverts():
        env.exchangeV3.fillOrder(
            order.getParams(), 
            order.takerAssetAmount, 
            order.sign(env.exchangeV3, testAccounts.testManager),
            { "from": testAccounts.WETHWhale }
        )

def test_cancel_order_success():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 4000e18, env.weth.address, 1e18)
    statusBefore = env.exchangeV3.getOrderInfo(order.getParams())[0]
    assert statusBefore == 3 # FILLABLE
    env.treasuryManager.cancelOrder(order.getParams(), {"from": testAccounts.testManager})
    statusAfter = env.exchangeV3.getOrderInfo(order.getParams())[0]
    assert statusAfter == 6 # CANCELLED

def test_cancel_order_non_manager():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.dai.transfer(env.treasuryManager.address, 10000e18, { "from": testAccounts.DAIWhale })
    env.weth.approve(env.exchangeV3.address, 2 ** 255, { "from": testAccounts.WETHWhale })
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 4000e18, env.weth.address, 1e18)
    statusBefore = env.exchangeV3.getOrderInfo(order.getParams())[0]
    assert statusBefore == 3 # FILLABLE
    with brownie.reverts():
        env.treasuryManager.cancelOrder(order.getParams(), {"from": env.deployer})
    statusAfter = env.exchangeV3.getOrderInfo(order.getParams())[0]
    assert statusAfter == 3 # FILLABLE

def test_invest_eth():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.approveBalancer({"from": env.deployer})
    env.treasuryManager.setPriceOracle(env.dai.address, '0x6085b0a8f4c7ffa2e8ca578037792d6535d1e29b', {"from": env.deployer})
    env.treasuryManager.setSlippageLimit(env.dai.address, 0.9e8, {"from": env.deployer})
    env.treasuryManager.setNOTEPurchaseLimit(0.9e8, {"from": env.deployer})
    env.weth.transfer(env.treasuryManager.address, 1e18, {"from": testAccounts.WETHWhale})
    env.note.approve(env.balancerVault.address, 2 ** 255, {"from": testAccounts.WETHWhale})
    # Initialize price oracle
    env.buyNOTE(1e8, testAccounts.WETHWhale)
    env.sellNOTE(1e8, testAccounts.WETHWhale)
    chain.sleep(3600)
    chain.mine()
    bptBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert pytest.approx(bptBefore, abs=1000) == 981770012526898092964803
    env.treasuryManager.investWETHAndNOTE(0.1e18, 0, 0, {"from": testAccounts.testManager})
    bptAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert pytest.approx(bptAfter, abs=1000) == 981846341102242643366015

def test_vebal():
    testAccounts = TestAccounts()
    env = create_environment()
    env.treasuryManager.setManager(testAccounts.testManager, { "from": env.deployer })
    env.treasuryManager.approveToken(env.dai.address, 2 ** 255, { "from": env.deployer })
    env.treasuryManager.approveBalancer({"from": env.deployer})
    env.bal.transfer(env.treasuryManager.address, 1000000e18, {"from": testAccounts.BALWhale})

    # Add liquidity
    assert env.balLiquidityToken.balanceOf(env.treasuryManager.address) == 0
    env.treasuryManager.addBalancerLiquidity(0, 1000e18, 0, {"from": testAccounts.testManager})
    assert pytest.approx(env.balLiquidityToken.balanceOf(env.treasuryManager.address), abs=1000) == 414349726186765950603

    # Delegate liquidity to VeBalDelegator
    env.treasuryManager.delegateBalancerLiquidity(
        env.balLiquidityToken.balanceOf(env.treasuryManager.address), 
        {"from": testAccounts.testManager}
    )
    assert env.balLiquidityToken.balanceOf(env.treasuryManager.address) == 0
    assert pytest.approx(env.balLiquidityToken.balanceOf(env.veBalDelegator.address), abs=1000) == 414349726186765950603

    # Withdraw liquidity from VeBalDelegator
    env.veBalDelegator.withdrawToManagerContract(2**256 - 1, {"from": env.sNOTE.owner()})
    assert env.balLiquidityToken.balanceOf(env.veBalDelegator.address) == 0
    assert pytest.approx(env.balLiquidityToken.balanceOf(env.treasuryManager.address), abs=1000) == 414349726186765950603

    # Remove liquidity
    env.treasuryManager.removeBalancerLiquidity(0, 0, 2**256 - 1, {"from": testAccounts.testManager})
    assert env.balLiquidityToken.balanceOf(env.treasuryManager.address) == 0
    assert pytest.approx(env.bal.balanceOf(env.treasuryManager.address), abs=1000) == 999798413393601360895808
    assert pytest.approx(env.weth.balanceOf(env.treasuryManager.address), abs=1000) == 979069248073433495
