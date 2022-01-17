import pytest
import brownie
import eth_abi
from brownie import accounts, sNOTE
from brownie.convert.datatypes import Wei
from brownie.network.state import Chain
from scripts.environment import TestAccounts, Environment, create_environment, ETH_ADDRESS

chain = Chain()
@pytest.fixture(autouse=True)
def run_around_tests():
    chain.snapshot()
    yield
    chain.revert()

def test_name_and_symbol():
    env = create_environment()
    assert env.sNOTE.name() == "Staked NOTE"
    assert env.sNOTE.symbol() == "sNOTE"

# Governance methods
def test_upgrade_snote():
    env = create_environment()
    testAccounts = TestAccounts()

    sNOTEImpl = sNOTE.deploy(
        env.balancerVault.address,
        env.poolId,
        env.note.address,
        env.weth.address,
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

    noteBefore = env.note.balanceOf(env.deployer)
    bptBefore = env.balancerPool.balanceOf(env.sNOTE.address)
    env.sNOTE.extractTokensForCollateralShortfall(bptBefore * 0.3, {"from": env.deployer})
    bptAfter = env.balancerPool.balanceOf(env.sNOTE.address)
    noteAfter = env.note.balanceOf(env.deployer)

    assert pytest.approx(bptAfter / bptBefore) == 0.70

    assert env.balancerPool.balanceOf(env.deployer) == 0
    assert pytest.approx(env.weth.balanceOf(env.deployer)) == 0.0006e18
    assert pytest.approx(noteAfter - noteBefore, abs=1) == 0.003e8

def test_extract_tokens_for_shortfall_cap():
    env = create_environment()
    testAccounts = TestAccounts()

    bptBefore = env.balancerPool.balanceOf(env.sNOTE.address)
    env.sNOTE.extractTokensForCollateralShortfall(bptBefore, {"from": env.deployer})
    bptAfter = env.balancerPool.balanceOf(env.sNOTE.address)
    assert pytest.approx(bptAfter / bptBefore, rel=1e-9) == 0.7
    assert env.balancerPool.balanceOf(env.deployer) == bptBefore - bptAfter

def test_set_swap_fee_percentage():
    env = create_environment()
    testAccounts = TestAccounts()

    with brownie.reverts("Ownable: caller is not the owner"):
        env.sNOTE.setSwapFeePercentage(0.03e18, {"from": testAccounts.ETHWhale})

    env.sNOTE.setSwapFeePercentage(0.03e18, {"from": env.deployer})
    assert env.balancerPool.getSwapFeePercentage() == 0.03e18

# User methods
def test_mint_from_bpt():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 100e8, {"from": env.deployer})
    env.note.approve(env.balancerVault.address, 2**256-1, {"from": testAccounts.ETHWhale})

    # [EXACT_TOKENS_IN_FOR_BPT_OUT, [ETH, NOTE], minBPTOut]
    userData = eth_abi.encode_abi(
        ['uint256', 'uint256[]', 'uint256'],
        [1, [0, Wei(1e8)], 0]
    )

    env.balancerVault.joinPool(
        env.poolId,
        testAccounts.ETHWhale,
        testAccounts.ETHWhale,
        (
            [ETH_ADDRESS, env.note.address],
            [0, 1e8],
            userData,
            False
        ),
        { "from": testAccounts.ETHWhale }
    )

    bptBalance = env.balancerPool.balanceOf(testAccounts.ETHWhale)
    env.balancerPool.approve(env.sNOTE.address, 2**255-1, {"from": testAccounts.ETHWhale})
    env.sNOTE.mintFromBPT(bptBalance, {"from": testAccounts.ETHWhale})

    assert env.balancerPool.balanceOf(testAccounts.ETHWhale) == 0
    assert env.sNOTE.balanceOf(testAccounts.ETHWhale) == bptBalance

def test_mint_from_note():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 100e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    env.sNOTE.mintFromNOTE(1e8, {"from": testAccounts.ETHWhale})
    # This should be the same as adding 1e8 NOTE above
    assert env.sNOTE.balanceOf(testAccounts.ETHWhale) == 566735618736030400

def test_pool_share_ratio():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.transfer(testAccounts.DAIWhale, 100e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.DAIWhale})

    env.sNOTE.mintFromNOTE(1e8, {"from": testAccounts.ETHWhale})
    env.sNOTE.mintFromNOTE(100e8, {"from": testAccounts.DAIWhale})

    sNOTEBalance1 = env.sNOTE.balanceOf(testAccounts.ETHWhale)
    poolTokenShare1 = env.sNOTE.getPoolTokenShare(sNOTEBalance1)
    sNOTEBalance2 = env.sNOTE.balanceOf(testAccounts.DAIWhale)
    poolTokenShare2 = env.sNOTE.getPoolTokenShare(sNOTEBalance2)
    # The relationship between sNOTEBalance2 and sNOTEBalance1 are non-linear due to 
    # slippage in the underlying balancer pool
    assert sNOTEBalance2 / sNOTEBalance1 == poolTokenShare2 / poolTokenShare1

@pytest.mark.skip
def test_increase_pool_share():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    env.sNOTE.mintFromNOTE(1e8, {"from": testAccounts.ETHWhale})
    poolTokenShare = env.sNOTE.poolTokenShareOf(testAccounts.ETHWhale)

    # NOTE whale generates some more BPT
    # [EXACT_TOKENS_IN_FOR_BPT_OUT, [ETH, NOTE], minBPTOut]
    userData = eth_abi.encode_abi(
        ['uint256', 'uint256[]', 'uint256'],
        [1, [0, Wei(10e8)], 0]
    )

    txn = env.balancerVault.joinPool(
        env.poolId,
        env.deployer,
        env.deployer,
        (
            [ETH_ADDRESS, env.note.address],
            [0, 10e8],
            userData,
            False
        ),
        { "from": env.deployer }
    )

    bptBalance = env.balancerPool.balanceOf(env.deployer.address)
    # Donates to the balance to sNOTE
    env.balancerPool.transfer(
        env.sNOTE.address,
        bptBalance,
        {"from": env.deployer.address}
    )

    newPoolTokenShare = env.sNOTE.poolTokenShareOf(testAccounts.ETHWhale)
    # TODO: This is some other multiple of the share...
    assert newPoolTokenShare / poolTokenShare == 10

def test_redeem():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    env.sNOTE.mintFromNOTE(1e8, {"from": testAccounts.ETHWhale})

    # Cannot redeem without cooldown
    with brownie.reverts("Cool Down Not Expired"):
        env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale), {"from": testAccounts.ETHWhale})

    env.sNOTE.startCoolDown({"from": testAccounts.ETHWhale})
    chain.mine(timestamp=(chain.time() + 5))

    # Cannot redeem before cooldown expires
    with brownie.reverts("Cool Down Not Expired"):
        env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale), {"from": testAccounts.ETHWhale})

    chain.mine(timestamp=(chain.time() + 100))
    # Successful redeem after cooldown expires
    env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale) / 2, {"from": testAccounts.ETHWhale})

    # Once a redemption occurs the cool down is reset
    with brownie.reverts("Cool Down Not Expired"):
        env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale), {"from": testAccounts.ETHWhale})

def test_transfer():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    env.sNOTE.mintFromNOTE(1e8, {"from": testAccounts.ETHWhale})
    env.sNOTE.transfer(env.deployer, 1e8, {"from": testAccounts.ETHWhale})
    assert env.sNOTE.balanceOf(env.deployer) == 1e8

def test_no_transfer_during_cooldown():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    env.sNOTE.mintFromNOTE(1e8, {"from": testAccounts.ETHWhale})
    env.sNOTE.startCoolDown({"from": testAccounts.ETHWhale})

    with brownie.reverts("Cool Down Not Expired"):
        env.sNOTE.transfer(env.deployer, 1e8, {"from": testAccounts.ETHWhale})

    # Transfer works after cooldown is stopped
    env.sNOTE.stopCoolDown({"from": testAccounts.ETHWhale})
    env.sNOTE.transfer(env.deployer, 1e8, {"from": testAccounts.ETHWhale})
    assert env.sNOTE.balanceOf(env.deployer) == 1e8

@pytest.mark.only
def test_cannot_redeem_more_than_max_bpt():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": env.deployer})

    env.sNOTE.mintFromNOTE(5e8, {"from": env.deployer})
    env.sNOTE.mintFromNOTE(1e8, {"from": testAccounts.ETHWhale})

    bptPoolShare = env.sNOTE.poolTokenShareOf(testAccounts.ETHWhale)
    (coolDownTime, maxBPTRedeem) = env.sNOTE.startCoolDown({"from": testAccounts.ETHWhale})
    assert maxBPTRedeem == bptPoolShare

    env.sNOTE.transfer(testAccounts.ETHWhale, env.sNOTE.balanceOf(env.deployer), {"from": env.deployer})

    assert env.sNOTE.poolTokenShareOf(testAccounts.ETHWhale) > maxBPTRedeem
    chain.mine(timestamp=(chain.time() + 100))

    with brownie.reverts():
        env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale) / 2, {"from": testAccounts.ETHWhale})

    assert False

def test_transfer_with_delegates():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    env.sNOTE.mintFromNOTE(1e8, {"from": testAccounts.ETHWhale})
    env.sNOTE.delegate(testAccounts.ETHWhale, {"from": testAccounts.ETHWhale})
    env.sNOTE.delegate(env.deployer, {"from": env.deployer})
    assert env.sNOTE.getVotes(testAccounts.ETHWhale) == env.sNOTE.balanceOf(testAccounts.ETHWhale)
    assert env.sNOTE.getVotes(env.deployer) == 0

    env.sNOTE.transfer(env.deployer, 1e8, {"from": testAccounts.ETHWhale})

    assert env.sNOTE.getVotes(testAccounts.ETHWhale) == env.sNOTE.balanceOf(testAccounts.ETHWhale)
    assert env.sNOTE.getVotes(env.deployer) == 1e8