
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
    order = Order(env.assetProxy, env.treasuryManager.address, env.dai.address, 4000e18, env.weth.address, 1e18)
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
    assert DAIBefore - DAIAfter == 4000e18
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
    pass

def test_trading_DAI_bad_taker_token():
    pass

def test_trading_DAI_bad_fee_recipient():
    pass

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
