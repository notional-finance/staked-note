from brownie import accounts, interface
from brownie.network.state import Chain
from scripts.environment import create_environment, TestAccounts

chain = Chain()

def test_single_depositor():
    testAccounts = TestAccounts()
    env = create_environment()

    env.veBalDelegator.setManagerContract(env.veBalDelegator.owner(), {"from": env.veBalDelegator.owner()})

    # Approve veBAL delegator
    guageWhale = accounts.at("0xee1e33029c2104993e4536be502990284e77080d", force=True)
    wstGaugeToken = interface.ERC20("0xcD4722B7c24C29e0413BDCd9e51404B4539D14aE")
    wstGaugeToken.approve(env.veBalDelegator.address, 2 ** 255, {"from": guageWhale})

    # Deposit LP token (can be done from vault controller contract)
    balanceBefore = wstGaugeToken.balanceOf(guageWhale.address)
    env.veBalDelegator.depositToken(wstGaugeToken.address, guageWhale.address, 10e18, {"from": env.veBalDelegator.owner()})
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, guageWhale.address) == 10e18
    assert wstGaugeToken.balanceOf(guageWhale.address) == balanceBefore - 10e18

    chain.sleep(16 * 24 * 3600)
    chain.mine()

    # Collect rewards
    lidoToken = interface.ERC20("0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32")
    assert lidoToken.balanceOf(env.veBalDelegator.address) == 0
    env.veBalDelegator.claimGaugeTokens(wstGaugeToken.address)
    assert lidoToken.balanceOf(env.veBalDelegator.address) >= 678963580280555990
    
    assert env.bal.balanceOf(env.veBalDelegator.address) == 0
    env.veBalDelegator.claimBAL(wstGaugeToken.address)
    assert env.bal.balanceOf(env.veBalDelegator.address) >= 1117624619526308444

    # Withdraw LP token
    env.veBalDelegator.withdrawToken(wstGaugeToken.address, guageWhale.address, 1e18, {"from": env.veBalDelegator.owner()})
    assert wstGaugeToken.balanceOf(guageWhale.address) == balanceBefore - 9e18
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, guageWhale.address) == 9e18
    env.veBalDelegator.withdrawToken(wstGaugeToken.address, guageWhale.address, 2 ** 256 - 1, {"from": env.veBalDelegator.owner()})
    assert wstGaugeToken.balanceOf(guageWhale.address) == balanceBefore
    assert env.veBalDelegator.getTokenBalance(wstGaugeToken.address, guageWhale.address) == 0
