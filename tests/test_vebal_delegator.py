import brownie
import pytest
import math
from brownie import accounts, interface
from brownie.network.state import Chain
from scripts.environment import create_environment, TestAccounts

chain = Chain()

@pytest.fixture(autouse=True)
def run_around_tests():
    chain.snapshot()
    yield
    chain.revert()

def test_single_depositor():
    testAccounts = TestAccounts()    
    env = create_environment()

    env.veBalDelegator.setManagerContract(testAccounts.DAIWhale.address, {"from": env.veBalDelegator.owner()})

    assert env.veBalDelegator.managerContract() == testAccounts.DAIWhale.address

    # Approve veBAL delegator
    gaugeWhale = accounts.at("0xee1e33029c2104993e4536be502990284e77080d", force=True)
    wstGaugeToken = interface.ERC20("0xcD4722B7c24C29e0413BDCd9e51404B4539D14aE")
    wstGaugeToken.approve(env.veBalDelegator.address, 2 ** 255, {"from": gaugeWhale})

    # Deposit LP token (can be done from vault controller contract)
    balanceBefore = wstGaugeToken.balanceOf(gaugeWhale.address)

    # Only manager contract can deposit
    with brownie.reverts():
        env.veBalDelegator.depositToken(wstGaugeToken.address, gaugeWhale.address, 10e18, {"from": env.veBalDelegator.owner()})

    env.veBalDelegator.depositToken(wstGaugeToken.address, gaugeWhale.address, 10e18, {"from": env.veBalDelegator.managerContract()})
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, gaugeWhale.address) == 10e18
    assert wstGaugeToken.balanceOf(gaugeWhale.address) == balanceBefore - 10e18

    chain.sleep(16 * 24 * 3600)
    chain.mine()

    # Collect rewards
    lidoToken = interface.ERC20("0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32")
    assert lidoToken.balanceOf(env.veBalDelegator.address) == 0

    with brownie.reverts():
        env.veBalDelegator.claimGaugeTokens(
            wstGaugeToken.address, 
            testAccounts.USDCWhale.address,
            {"from": env.veBalDelegator.owner()}
        )

    tx = env.veBalDelegator.claimGaugeTokens(
        wstGaugeToken.address, 
        testAccounts.USDCWhale.address, 
        {"from": env.veBalDelegator.managerContract()}
    )
    assert tx.return_value[0][0] == lidoToken.address
    assert tx.return_value[1][0] >= 678963580280555990
    assert lidoToken.balanceOf(env.veBalDelegator.address) == 0
    assert lidoToken.balanceOf(testAccounts.USDCWhale.address) >= 678963580280555990

    with brownie.reverts():
        env.veBalDelegator.claimBAL(
            wstGaugeToken.address,
            testAccounts.USDCWhale.address,
            {"from": env.veBalDelegator.owner()}
        )

    assert env.bal.balanceOf(env.veBalDelegator.address) == 0
    tx = env.veBalDelegator.claimBAL(
        wstGaugeToken.address, 
        testAccounts.USDCWhale.address, 
        {"from": env.veBalDelegator.managerContract()}
    )
    assert tx.return_value >= 1117624619526308444
    assert env.bal.balanceOf(env.veBalDelegator.address) == 0
    assert env.bal.balanceOf(testAccounts.USDCWhale.address) >= 1117624619526308444

    # Withdraw LP token
    env.veBalDelegator.withdrawToken(wstGaugeToken.address, gaugeWhale.address, 1e18, {"from": env.veBalDelegator.managerContract()})
    assert wstGaugeToken.balanceOf(gaugeWhale.address) == balanceBefore - 9e18
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, gaugeWhale.address) == 9e18

    with brownie.reverts():
        env.veBalDelegator.withdrawToken(wstGaugeToken.address, gaugeWhale.address, 2 ** 256 - 1, {"from": env.veBalDelegator.owner()})

    env.veBalDelegator.withdrawToken(wstGaugeToken.address, gaugeWhale.address, 2 ** 256 - 1, {"from": env.veBalDelegator.managerContract()})
    assert wstGaugeToken.balanceOf(gaugeWhale.address) == balanceBefore
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, gaugeWhale.address) == 0

def test_multiple_depositors():
    testAccounts = TestAccounts()    
    env = create_environment()

    env.veBalDelegator.setManagerContract(testAccounts.DAIWhale.address, {"from": env.veBalDelegator.owner()})

    wstGaugeToken = interface.ERC20("0xcD4722B7c24C29e0413BDCd9e51404B4539D14aE")

    # Approve veBAL delegator
    gaugeWhale1 = accounts.at("0xee1e33029c2104993e4536be502990284e77080d", force=True)
    wstGaugeToken.approve(env.veBalDelegator.address, 2 ** 255, {"from": gaugeWhale1})
    balance1 = wstGaugeToken.balanceOf(gaugeWhale1)
 
    gaugeWhale2 = accounts.at("0x40dcba8e2508ddaa687fc26f9491b8cca563c845", force=True)
    wstGaugeToken.approve(env.veBalDelegator.address, 2 ** 255, {"from": gaugeWhale2})
    balance2 = wstGaugeToken.balanceOf(gaugeWhale2)
    balance2Half = math.floor(balance2 / 2)

    env.veBalDelegator.depositToken(wstGaugeToken.address, gaugeWhale1.address, balance1, {"from": env.veBalDelegator.managerContract()})
    env.veBalDelegator.depositToken(wstGaugeToken.address, gaugeWhale2.address, balance2Half, {"from": env.veBalDelegator.managerContract()})
    env.veBalDelegator.depositToken(wstGaugeToken.address, gaugeWhale2.address, balance2 - balance2Half, {"from": env.veBalDelegator.managerContract()})

    assert wstGaugeToken.balanceOf(env.veBalDelegator) == balance1 + balance2
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, gaugeWhale1.address) == balance1
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, gaugeWhale2.address) == balance2

    chain.sleep(16 * 24 * 3600)
    chain.mine()

    # Collect rewards
    lidoToken = interface.ERC20("0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32")
    assert lidoToken.balanceOf(env.veBalDelegator.address) == 0

    with brownie.reverts():
        env.veBalDelegator.claimGaugeTokens(
            wstGaugeToken.address, 
            testAccounts.USDCWhale.address, 
            {"from": env.veBalDelegator.owner()}
        )

    tx = env.veBalDelegator.claimGaugeTokens(
        wstGaugeToken.address, 
        testAccounts.USDCWhale.address, 
        {"from": env.veBalDelegator.managerContract()}
    )
    assert tx.return_value[0][0] == lidoToken.address
    assert tx.return_value[1][0] >= 49052628368936787766
    assert lidoToken.balanceOf(env.veBalDelegator.address) == 0
    assert lidoToken.balanceOf(testAccounts.USDCWhale.address) >= 49052628368936787766

    with brownie.reverts():
        env.veBalDelegator.claimBAL(
            wstGaugeToken.address, 
            testAccounts.USDCWhale.address, 
            {"from": env.veBalDelegator.owner()}
        )

    assert env.bal.balanceOf(env.veBalDelegator.address) == 0
    tx = env.veBalDelegator.claimBAL(
        wstGaugeToken.address, 
        testAccounts.USDCWhale.address, 
        {"from": env.veBalDelegator.managerContract()}
    )
    assert tx.return_value >= 80578702484131086358
    assert env.bal.balanceOf(env.veBalDelegator.address) == 0
    assert env.bal.balanceOf(testAccounts.USDCWhale.address) >= 80578702484131086358

    # Withdraw LP token
    with brownie.reverts():
        env.veBalDelegator.withdrawToken(wstGaugeToken.address, gaugeWhale1.address, 2**256-1, {"from": env.veBalDelegator.owner()})            

    env.veBalDelegator.withdrawToken(wstGaugeToken.address, gaugeWhale1.address, 2**256-1, {"from": env.veBalDelegator.managerContract()})
    assert wstGaugeToken.balanceOf(gaugeWhale1.address) == balance1
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, gaugeWhale1.address) == 0

    env.veBalDelegator.withdrawToken(wstGaugeToken.address, gaugeWhale2.address, balance2Half, {"from": env.veBalDelegator.managerContract()})
    assert wstGaugeToken.balanceOf(gaugeWhale2.address) == balance2Half
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, gaugeWhale2.address) == balance2 - balance2Half

    env.veBalDelegator.withdrawToken(wstGaugeToken.address, gaugeWhale2.address, 2**256-1, {"from": env.veBalDelegator.managerContract()})
    assert wstGaugeToken.balanceOf(gaugeWhale2.address) == balance2
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, gaugeWhale2.address) == 0
