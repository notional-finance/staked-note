import pytest
import brownie
from brownie import accounts, sNOTE
from brownie.network.state import Chain
from scripts.environment import TestAccounts, Environment, create_environment

chain = Chain()
@pytest.fixture(autouse=True)
def run_around_tests():
    chain.snapshot()
    yield
    chain.revert()

# Governance methods
def test_upgrade_snote():
    env = create_environment()
    testAccounts = TestAccounts()

    sNOTEImpl = sNOTE.deploy(
        env.balancerVault.address,
        env.poolId,
        env.note.address,
        {"from": env.deployer}
    )

    with brownie.reverts("Ownable: caller is not the owner"):
        env.sNOTE.upgradeTo(sNOTEImpl.address, {"from": testAccounts.ETHWhale})

    env.sNOTE.upgradeTo(sNOTEImpl.address, {"from": env.deployer})
    
def test_set_cooldown_time():
    env = create_environment()
    testAccounts = TestAccounts()

    with brownie.reverts("Ownable: caller is not the owner"):
        env.sNOTE.setCoolDownTime(200, {"from": testAccounts.ETHWhale})

    env.sNOTE.setCoolDownTime(200, {"from": env.deployer})
    assert env.sNOTE.coolDownTimeInSeconds() == 200

def test_extract_tokens_for_shortfall():
    env = create_environment()
    testAccounts = TestAccounts()

    with brownie.reverts("Ownable: caller is not the owner"):
        env.sNOTE.extractTokensForCollateralShortfall(1, {"from": testAccounts.ETHWhale})

    bptBefore = env.balancerPool.balanceOf(env.sNOTE.address)
    env.sNOTE.extractTokensForCollateralShortfall(100, {"from": env.deployer})
    bptAfter = env.balancerPool.balanceOf(env.sNOTE.address)
    assert bptBefore - bptAfter == 100
    assert env.balancerPool.balanceOf(env.deployer) == 100

def test_extract_tokens_for_shortfall_cap():
    env = create_environment()
    testAccounts = TestAccounts()

    bptBefore = env.balancerPool.balanceOf(env.sNOTE.address)
    env.sNOTE.extractTokensForCollateralShortfall(bptBefore, {"from": env.deployer})
    bptAfter = env.balancerPool.balanceOf(env.sNOTE.address)
    assert bptAfter / bptBefore == 0.7
    assert env.balancerPool.balanceOf(env.deployer) == bptBefore - bptAfter

def test_set_swap_fee_percentage():
    env = create_environment()
    testAccounts = TestAccounts()

    with brownie.reverts("Ownable: caller is not the owner"):
        env.sNOTE.setSwapFeePercentage(0.03e18, {"from": testAccounts.ETHWhale})

    env.sNOTE.setSwapFeePercentage(0.03e18, {"from": env.deployer})
    assert env.balancerPool.getSwapFeePercentage() == 0.03e18

# # User methods
# def test_mint_from_bpt():
# def test_mint_from_note():
# def test_redeem():
# def test_no_transfer_during_cooldown():
# def test_transfer_with_delegates():