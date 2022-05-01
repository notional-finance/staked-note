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
        0,
        1,
        env.sNOTE.LIQUIDITY_GAUGE(),
        env.sNOTE.TREASURY_MANAGER_CONTRACT(),
        env.sNOTE.BALANCER_MINTER(),
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

    feeCollectorBefore = env.note.balanceOf(env.balancerVault.getProtocolFeesCollector())
    poolNoteBefore = env.balancerVault.getPoolTokenInfo(env.poolId, env.note.address).dict()["cash"]
    poolWethBefore = env.balancerVault.getPoolTokenInfo(env.poolId, env.weth.address).dict()["cash"]
    wethBefore = env.weth.balanceOf(env.deployer)
    noteBefore = env.note.balanceOf(env.deployer)
    bptBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    env.sNOTE.extractTokensForCollateralShortfall(bptBefore * 0.3, {"from": env.deployer})
    bptAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    noteAfter = env.note.balanceOf(env.deployer)
    wethAfter = env.weth.balanceOf(env.deployer)
    poolNoteAfter = env.balancerVault.getPoolTokenInfo(env.poolId, env.note.address).dict()["cash"]
    poolWethAfter = env.balancerVault.getPoolTokenInfo(env.poolId, env.weth.address).dict()["cash"]
    feeCollectorAfter = env.note.balanceOf(env.balancerVault.getProtocolFeesCollector())
    noteFee = feeCollectorAfter - feeCollectorBefore

    assert pytest.approx(bptAfter / bptBefore) == 0.70

    assert wethAfter - wethBefore == poolWethBefore - poolWethAfter
    assert pytest.approx(poolWethAfter / poolWethBefore, rel=1e2) == 0.70
    assert noteAfter - noteBefore + noteFee == poolNoteBefore - poolNoteAfter
    assert pytest.approx(poolNoteAfter / poolNoteBefore, rel=1e2) == 0.70

    with brownie.reverts("Shortfall Cooldown"):
        env.sNOTE.extractTokensForCollateralShortfall(bptBefore * 0.3, {"from": env.deployer})

    # Can extract again after shortfall window passes
    chain.mine(1, timestamp=chain.time() + 86400 * 8)
    env.sNOTE.extractTokensForCollateralShortfall(1e8, {"from": env.deployer})


def test_extract_tokens_for_shortfall_cap():
    env = create_environment()
    testAccounts = TestAccounts()

    bptBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    env.sNOTE.extractTokensForCollateralShortfall(bptBefore, {"from": env.deployer})
    bptAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert pytest.approx(bptAfter / bptBefore, rel=1e-9) == 0.5

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

    assert env.sNOTE.balanceOf(testAccounts.ETHWhale) == 0
    # Make sure BPT is staked
    gaugeBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    txn = env.sNOTE.mintFromBPT(bptBalance, {"from": testAccounts.ETHWhale})
    gaugeAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert (gaugeAfter - gaugeBefore) == bptBalance
    assert env.balancerPool.balanceOf(env.sNOTE.address) == 0

    assert txn.events["SNoteMinted"]["account"] == testAccounts.ETHWhale
    assert pytest.approx(txn.events["SNoteMinted"]["wethChangeAmount"], abs=1000) == 56226467271023
    assert pytest.approx(txn.events["SNoteMinted"]["noteChangeAmount"], abs=10) == 79919995
    assert txn.events["SNoteMinted"]["bptChangeAmount"] == bptBalance

    assert env.balancerPool.balanceOf(testAccounts.ETHWhale) == 0
    assert pytest.approx(env.sNOTE.getPoolTokenShare(env.sNOTE.balanceOf(testAccounts.ETHWhale)), abs=100) == bptBalance

def test_pool_share_ratio():
    env = create_environment(useFresh = True)
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 150e8, {"from": env.deployer})
    env.note.transfer(testAccounts.DAIWhale, 100e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.DAIWhale})

    # [EXACT_TOKENS_IN_FOR_BPT_OUT, [ETH, NOTE], minBPTOut]
    env.note.approve(env.balancerVault.address, 2**256-1, {"from": testAccounts.ETHWhale})
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
            [0, 50e8],
            userData,
            False
        ),
        { "from": testAccounts.ETHWhale }
    )

    assert env.sNOTE.totalSupply() == 0
    initialBPTBalance = env.liquidityGauge.balanceOf(env.sNOTE.address)

    txn1 = env.sNOTE.mintFromETH(100e8, 0, {"from": testAccounts.ETHWhale})
    bptFrom1 = txn1.events['Transfer'][1]['value']
    bptAdded = env.balancerPool.balanceOf(testAccounts.ETHWhale) / 2

    env.balancerPool.transfer(env.sNOTE.address, bptAdded, {"from": testAccounts.ETHWhale})

    # stakeAll must be called after donating BPT to sNOTE
    env.sNOTE.stakeAll({"from": env.deployer})

    txn2 = env.sNOTE.mintFromETH(100e8, 0, {"from": testAccounts.DAIWhale})
    bptFrom2 = txn2.events['Transfer'][1]['value']

    # Test that the pool share of the second minter does not accrue balances of those from the first
    poolTokenShare1 = env.sNOTE.poolTokenShareOf(testAccounts.ETHWhale)
    poolTokenShare2 = env.sNOTE.poolTokenShareOf(testAccounts.DAIWhale)

    assert pytest.approx(poolTokenShare1, abs=1) == bptFrom1 + bptAdded + initialBPTBalance
    assert pytest.approx(poolTokenShare2, abs=1) == bptFrom2

    bptAdded2 = env.balancerPool.balanceOf(testAccounts.ETHWhale)

    # Test that additional tokens are split between the two holders proportionally
    env.balancerPool.transfer(env.sNOTE.address, bptAdded2, {"from": testAccounts.ETHWhale})

    # stakeAll must be called after donating BPT to sNOTE
    env.sNOTE.stakeAll({"from": env.deployer})

    sNOTEBalance1 = env.sNOTE.balanceOf(testAccounts.ETHWhale)
    sNOTEBalance2 = env.sNOTE.balanceOf(testAccounts.DAIWhale)
    totalSupply = env.sNOTE.totalSupply()
    poolTokenShare3 = env.sNOTE.poolTokenShareOf(testAccounts.ETHWhale)
    poolTokenShare4 = env.sNOTE.poolTokenShareOf(testAccounts.DAIWhale)
    assert pytest.approx(poolTokenShare3, abs=1000) == bptFrom1 + bptAdded + initialBPTBalance + (bptAdded2 * sNOTEBalance1 / totalSupply)
    assert pytest.approx(poolTokenShare4, abs=1000) == bptFrom2 + (bptAdded2 * sNOTEBalance2 / totalSupply)

def test_mint_from_note_and_eth():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 100e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    gaugeBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    txn = env.sNOTE.mintFromETH(1e8, 0, {"from": testAccounts.ETHWhale, "value": 1e18})
    gaugeAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert (gaugeAfter - gaugeBefore) == txn.events['SNoteMinted'][0]['bptChangeAmount']
    assert env.sNOTE.balanceOf(testAccounts.ETHWhale) > 0

def test_mint_from_note():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 100e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    gaugeBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    txn = env.sNOTE.mintFromETH(1e8, 0,{"from": testAccounts.ETHWhale, "value": 0})
    gaugeAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert (gaugeAfter - gaugeBefore) == txn.events['SNoteMinted'][0]['bptChangeAmount']
    assert env.sNOTE.balanceOf(testAccounts.ETHWhale) > 0

def test_mint_from_eth():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 100e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    gaugeBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    txn = env.sNOTE.mintFromETH(0, 0, {"from": testAccounts.ETHWhale, "value": 1e18})
    gaugeAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert (gaugeAfter - gaugeBefore) == txn.events['SNoteMinted'][0]['bptChangeAmount']
    assert env.sNOTE.balanceOf(testAccounts.ETHWhale) > 0

def test_mint_from_weth():
    env = create_environment()
    testAccounts = TestAccounts()
    env.weth.approve(env.sNOTE.address, 2**255 - 1, {"from": testAccounts.WETHWhale})

    gaugeBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    txn = env.sNOTE.mintFromWETH(0, 1e18, 0, {"from": testAccounts.WETHWhale})
    gaugeAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert (gaugeAfter - gaugeBefore) == txn.events['SNoteMinted'][0]['bptChangeAmount']
    assert env.sNOTE.balanceOf(testAccounts.WETHWhale) > 0

def test_mint_from_weth_and_note():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.WETHWhale, 100e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256 - 1, {"from": testAccounts.WETHWhale})
    env.weth.approve(env.sNOTE.address, 2**255 - 1, {"from": testAccounts.WETHWhale})

    gaugeBefore = env.liquidityGauge.balanceOf(env.sNOTE.address)
    txn = env.sNOTE.mintFromWETH(1e8, 1e18, 0, {"from": testAccounts.WETHWhale})
    gaugeAfter = env.liquidityGauge.balanceOf(env.sNOTE.address)
    assert (gaugeAfter - gaugeBefore) == txn.events['SNoteMinted'][0]['bptChangeAmount']
    assert txn.events["SNoteMinted"]["account"] == testAccounts.WETHWhale
    assert txn.events["SNoteMinted"]["wethChangeAmount"] == 1e18
    assert txn.events["SNoteMinted"]["noteChangeAmount"] == 1e8
    poolTokenShare = env.sNOTE.getPoolTokenShare(env.sNOTE.balanceOf(testAccounts.WETHWhale))
    assert pytest.approx(txn.events["SNoteMinted"]["bptChangeAmount"], abs=10) == poolTokenShare

def test_no_mint_during_cooldown():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    env.sNOTE.startCoolDown({"from": testAccounts.ETHWhale})

    with brownie.reverts("Account in Cool Down"):
        env.sNOTE.mintFromETH(1e8, 0,{"from": testAccounts.ETHWhale})
        env.sNOTE.mintFromWETH(1e8, 0, 0, {"from": testAccounts.ETHWhale})

def test_redeem():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    txn = env.sNOTE.mintFromETH(1e8, 0,{"from": testAccounts.ETHWhale})
    assert txn.events["SNoteMinted"]["account"] == testAccounts.ETHWhale
    assert txn.events["SNoteMinted"]["wethChangeAmount"] == 0
    assert txn.events["SNoteMinted"]["noteChangeAmount"] == 1e8

    # Cannot redeem without cooldown
    with brownie.reverts("Not in Redemption Window"):
        env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale), 0, 0, True, {"from": testAccounts.ETHWhale})

    env.sNOTE.startCoolDown({"from": testAccounts.ETHWhale})
    chain.mine(timestamp=(chain.time() + 5))

    # Cannot redeem before window begins
    with brownie.reverts("Not in Redemption Window"):
        env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale), 0, 0, True, {"from": testAccounts.ETHWhale})

    coolDownTime = env.sNOTE.coolDownTimeInSeconds()
    chain.mine(timestamp=(chain.time() + coolDownTime))

    ethBalBefore = testAccounts.ETHWhale.balance()
    noteBalBefore = env.note.balanceOf(testAccounts.ETHWhale)
    wethBalBefore = env.weth.balanceOf(testAccounts.ETHWhale)

    poolTokenShare = env.sNOTE.getPoolTokenShare(env.sNOTE.balanceOf(testAccounts.ETHWhale))
    [ethAmount, noteAmount1] = env.sNOTE.getTokenClaim(env.sNOTE.balanceOf(testAccounts.ETHWhale) / 2)
    # Successful redeem after window begins (redeem to ETH)
    env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale) / 2, 0, 0, True, {"from": testAccounts.ETHWhale})

    poolTokenShare = env.sNOTE.getPoolTokenShare(env.sNOTE.balanceOf(testAccounts.ETHWhale))
    [wethAmount, noteAmount2] = env.sNOTE.getTokenClaim(env.sNOTE.balanceOf(testAccounts.ETHWhale) / 2)
    # Successful redeem again within window (redeem to WETH)
    env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale) / 2, 0, 0, False, {"from": testAccounts.ETHWhale})

    ethBalAfter = testAccounts.ETHWhale.balance()
    noteBalAfter = env.note.balanceOf(testAccounts.ETHWhale)
    wethBalAfter = env.weth.balanceOf(testAccounts.ETHWhale)

    assert pytest.approx(ethBalAfter - ethBalBefore, abs=1000) == ethAmount
    assert pytest.approx(noteBalAfter - noteBalBefore, abs=1000) == noteAmount1 + noteAmount2
    assert pytest.approx(wethBalAfter - wethBalBefore, abs=1000) == wethAmount

    # Leave redemption window
    chain.mine(timestamp=(chain.time() + 86400 * 3))

    # Once a redemption occurs the cool down is reset
    with brownie.reverts("Not in Redemption Window"):
        env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale), 0, 0, True, {"from": testAccounts.ETHWhale})

def test_transfer():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    txn = env.sNOTE.mintFromETH(1e8, 0,{"from": testAccounts.ETHWhale})
    assert txn.events["SNoteMinted"]["account"] == testAccounts.ETHWhale
    assert txn.events["SNoteMinted"]["wethChangeAmount"] == 0
    assert txn.events["SNoteMinted"]["noteChangeAmount"] == 100000000
    env.sNOTE.transfer(env.deployer, 1e8, {"from": testAccounts.ETHWhale})
    assert env.sNOTE.balanceOf(env.deployer) == 1e8

def test_no_transfer_during_cooldown():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    txn = env.sNOTE.mintFromETH(1e8, 0,{"from": testAccounts.ETHWhale})
    assert txn.events["SNoteMinted"]["account"] == testAccounts.ETHWhale
    assert txn.events["SNoteMinted"]["wethChangeAmount"] == 0
    assert txn.events["SNoteMinted"]["noteChangeAmount"] == 1e8
    env.sNOTE.startCoolDown({"from": testAccounts.ETHWhale})

    with brownie.reverts("Account in Cool Down"):
        env.sNOTE.transfer(env.deployer, 1e8, {"from": testAccounts.ETHWhale})

    # Transfer works after cooldown is stopped
    env.sNOTE.stopCoolDown({"from": testAccounts.ETHWhale})
    env.sNOTE.transfer(env.deployer, 1e8, {"from": testAccounts.ETHWhale})
    assert env.sNOTE.balanceOf(env.deployer) == 1e8

def test_transfer_with_delegates():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    txn = env.sNOTE.mintFromETH(1e8, 0,{"from": testAccounts.ETHWhale})
    
    # Sleep through the oracle window
    # TODO: remove after full oracle initialization
    chain.sleep(env.sNOTE.VOTING_POWER_ORACLE_SECONDS() + 1)
    chain.mine()

    assert txn.events["SNoteMinted"]["account"] == testAccounts.ETHWhale
    assert txn.events["SNoteMinted"]["wethChangeAmount"] == 0
    assert txn.events["SNoteMinted"]["noteChangeAmount"] == 1e8
    env.sNOTE.delegate(testAccounts.ETHWhale, {"from": testAccounts.ETHWhale})
    env.sNOTE.delegate(env.deployer, {"from": env.deployer})
    votesStarting = env.sNOTE.getVotes(testAccounts.ETHWhale)
    assert env.sNOTE.getVotes(env.deployer) == 0

    env.sNOTE.transfer(env.deployer, env.sNOTE.balanceOf(testAccounts.ETHWhale), {"from": testAccounts.ETHWhale})

    assert env.sNOTE.getVotes(testAccounts.ETHWhale) == 0
    assert env.sNOTE.getVotes(env.deployer) == votesStarting

def test_cannot_transfer_inside_redeem_window():
    env = create_environment()
    testAccounts = TestAccounts()
    env.note.transfer(testAccounts.ETHWhale, 1e8, {"from": env.deployer})
    env.note.approve(env.sNOTE.address, 2**256-1, {"from": testAccounts.ETHWhale})

    txn = env.sNOTE.mintFromETH(1e8, 0,{"from": testAccounts.ETHWhale})
    assert txn.events["SNoteMinted"]["account"] == testAccounts.ETHWhale
    assert txn.events["SNoteMinted"]["wethChangeAmount"] == 0
    assert txn.events["SNoteMinted"]["noteChangeAmount"] == 1e8
    env.sNOTE.startCoolDown({"from": testAccounts.ETHWhale})

    coolDownTime = env.sNOTE.coolDownTimeInSeconds() + 100
    chain.mine(timestamp=(chain.time() + coolDownTime))

    # Successful redeem to show that we are in the window
    poolTokenShare = env.sNOTE.getPoolTokenShare(env.sNOTE.balanceOf(testAccounts.ETHWhale))
    [wethAmount, noteAmount] = env.sNOTE.getTokenClaim(env.sNOTE.balanceOf(testAccounts.ETHWhale) / 2)
    txn = env.sNOTE.redeem(env.sNOTE.balanceOf(testAccounts.ETHWhale) / 2, 0, 0, True, {"from": testAccounts.ETHWhale})
    # Withdrawing more WETH and NOTE because of donated initial liquidity
    assert txn.events["SNoteRedeemed"]["account"] == testAccounts.ETHWhale
    assert pytest.approx(txn.events["SNoteRedeemed"]["wethChangeAmount"], abs=1000) == wethAmount
    assert pytest.approx(txn.events["SNoteRedeemed"]["noteChangeAmount"], abs=1000) == noteAmount
    assert pytest.approx(txn.events["SNoteRedeemed"]["bptChangeAmount"], abs=1000) == poolTokenShare / 2

    # Cannot transfer tokens even during the redemption window
    with brownie.reverts("Account in Cool Down"):
        env.sNOTE.transfer(env.deployer, env.sNOTE.balanceOf(testAccounts.ETHWhale), {"from": testAccounts.ETHWhale})

    chain.mine(timestamp=(chain.time() + 86400 * 3))

    # Can transfer once you leave the redemption window
    env.sNOTE.transfer(env.deployer, env.sNOTE.balanceOf(testAccounts.ETHWhale), {"from": testAccounts.ETHWhale})

def test_get_voting_power_single_staker_price_increasing():
    env = create_environment()
    testAccounts = TestAccounts()
    env.weth.approve(env.balancerVault.address, 2 ** 255, {"from": testAccounts.WETHWhale})
    env.note.approve(env.sNOTEProxy.address, 2 ** 255, {"from": testAccounts.WETHWhale})
    env.note.approve(env.balancerVault.address, 2 ** 255, {"from": testAccounts.WETHWhale})
    
    env.buyNOTE(1e8, testAccounts.WETHWhale)

    env.sNOTE.mintFromETH(env.note.balanceOf(testAccounts.WETHWhale), 0, {"from": testAccounts.WETHWhale})
    assert pytest.approx(env.sNOTE.balanceOf(testAccounts.WETHWhale), abs=1000) == 41357276133699717

    supplyShare = env.sNOTE.balanceOf(testAccounts.WETHWhale) / env.sNOTE.totalSupply()
    assert pytest.approx(supplyShare, abs=1e-9) == 2.1248363030395777e-07

    # Sleep through the oracle window
    # TODO: remove after full oracle initialization
    chain.sleep(env.sNOTE.VOTING_POWER_ORACLE_SECONDS() + 1)
    chain.mine()

    # Check voting power of the entire supply
    noteBalance = env.balancerVault.getPoolTokens(env.poolId)[1][1]
    totalVotingPower = env.sNOTE.getVotingPower(env.sNOTE.totalSupply())
    assert totalVotingPower < noteBalance 
    assert pytest.approx(totalVotingPower, abs=100) == 376134463577018

    # Check voting power of the account
    votingPower = env.sNOTE.getVotingPower(env.sNOTE.balanceOf(testAccounts.WETHWhale))
    assert pytest.approx(votingPower, abs=100) == 79922416
    assert pytest.approx(votingPower / totalVotingPower, abs=1e-9) == supplyShare

    # Increase NOTE price
    env.buyNOTE(5e8, testAccounts.WETHWhale)

    env.sNOTE.mintFromETH(env.note.balanceOf(testAccounts.WETHWhale), 0, {"from": testAccounts.WETHWhale})
    assert pytest.approx(env.sNOTE.balanceOf(testAccounts.WETHWhale), abs=1000) == 248143912401637857

    supplyShare = env.sNOTE.balanceOf(testAccounts.WETHWhale) / env.sNOTE.totalSupply()
    assert pytest.approx(supplyShare, abs=1e-8) == 1.274901740551103e-06

    # Sleep through the oracle window
    # TODO: remove after full oracle initialization
    chain.sleep(env.sNOTE.VOTING_POWER_ORACLE_SECONDS() + 1)
    chain.mine()

    # Check voting power of the entire supply
    noteBalance = env.balancerVault.getPoolTokens(env.poolId)[1][1]
    totalVotingPower = env.sNOTE.getVotingPower(env.sNOTE.totalSupply())
    assert totalVotingPower < noteBalance 
    assert pytest.approx(totalVotingPower, abs=1000) == 376134863189594

    # Check voting power of the account
    votingPower = env.sNOTE.votingPowerWithoutDelegation(testAccounts.WETHWhale)
    assert pytest.approx(votingPower, abs=100) == 479534991
    assert pytest.approx(votingPower / totalVotingPower, abs=1e-8) == supplyShare

def test_get_voting_power_single_staker_price_decreasing_fast():
    env = create_environment()
    testAccounts = TestAccounts()
    env.weth.transfer(testAccounts.NOTEWhale.address, 100e18, {"from": testAccounts.WETHWhale})
    env.note.approve(env.balancerVault.address, 2 ** 255, {"from": testAccounts.NOTEWhale})
    env.note.approve(env.sNOTEProxy.address, 2 ** 255, {"from": testAccounts.NOTEWhale})
    env.note.approve(env.balancerVault.address, 2 ** 255, {"from": testAccounts.WETHWhale})

    env.sNOTE.mintFromETH(10e8, 0, {"from": testAccounts.NOTEWhale})
    assert env.balancerPool.balanceOf(env.sNOTE) == 0
    assert pytest.approx(env.sNOTE.balanceOf(testAccounts.NOTEWhale), abs=1000) == 413572590035542476

    supplyShare = env.sNOTE.balanceOf(testAccounts.NOTEWhale) / env.sNOTE.totalSupply()
    assert pytest.approx(supplyShare, abs=1e-8) == 2.1248313595092895e-06

    env.sellNOTE(5e8, testAccounts.NOTEWhale)

    # Sleep through the oracle window
    # TODO: remove after full oracle initialization
    chain.sleep(env.sNOTE.VOTING_POWER_ORACLE_SECONDS() + 1)
    chain.mine()

    # Check voting power of the entire supply
    noteBalance = env.balancerVault.getPoolTokens(env.poolId)[1][1]
    totalVotingPower = env.sNOTE.getVotingPower(env.sNOTE.totalSupply())
    assert totalVotingPower < noteBalance 
    assert pytest.approx(totalVotingPower, abs=1000) == 376135182878434

    # Check voting power of the account
    votingPower = env.sNOTE.votingPowerWithoutDelegation(testAccounts.NOTEWhale)
    assert pytest.approx(votingPower, abs=100) == 799223831
    assert pytest.approx(votingPower / totalVotingPower, abs=1e-8) == supplyShare


def test_get_voting_power_single_staker_price_decreasing_slow():
    env = create_environment()
    testAccounts = TestAccounts()
    env.weth.transfer(testAccounts.NOTEWhale.address, 100e18, {"from": testAccounts.WETHWhale})
    env.note.approve(env.balancerVault.address, 2 ** 255, {"from": testAccounts.NOTEWhale})
    env.note.approve(env.sNOTEProxy.address, 2 ** 255, {"from": testAccounts.NOTEWhale})
    env.note.approve(env.balancerVault.address, 2 ** 255, {"from": testAccounts.WETHWhale})

    env.sNOTE.mintFromETH(10e8, 0, {"from": testAccounts.NOTEWhale})
    assert pytest.approx(env.sNOTE.balanceOf(testAccounts.NOTEWhale), abs=1000) == 413572590035542476

    supplyShare = env.sNOTE.balanceOf(testAccounts.NOTEWhale) / env.sNOTE.totalSupply()
    assert pytest.approx(supplyShare, abs=1e-8) == 2.1248313595092895e-06

    # Oracle price is not affected without a certain amount of delay
    env.sellNOTE(1e8, testAccounts.NOTEWhale)
    chain.sleep(3600)
    chain.mine()
    env.sellNOTE(1e8, testAccounts.NOTEWhale)
    chain.sleep(3600)
    chain.mine()
    env.sellNOTE(1e8, testAccounts.NOTEWhale)
    chain.sleep(3600)
    chain.mine()
    env.sellNOTE(1e8, testAccounts.NOTEWhale)
    chain.sleep(3600)
    chain.mine()
    env.sellNOTE(1e8, testAccounts.NOTEWhale)
    chain.sleep(3600)
    chain.mine()

    # Sleep through the oracle window
    # TODO: remove after full oracle initialization
    chain.sleep(env.sNOTE.VOTING_POWER_ORACLE_SECONDS() + 1)
    chain.mine()

    # Check voting power of the entire supply
    noteBalance = env.balancerVault.getPoolTokens(env.poolId)[1][1]
    totalVotingPower = env.sNOTE.getVotingPower(env.sNOTE.totalSupply())
    assert totalVotingPower < noteBalance 
    assert pytest.approx(totalVotingPower, abs=1000) == 376135182878434

    # Check voting power of the account
    votingPower = env.sNOTE.votingPowerWithoutDelegation(testAccounts.NOTEWhale)
    assert pytest.approx(votingPower, abs=100) == 799223831
    assert pytest.approx(votingPower / totalVotingPower, abs=1e-8) == supplyShare

# BALANCER_MINTER.mint(address(LIQUIDITY_GAUGE)) is failing
@pytest.mark.skip(reason="NOTE/ETH liquidity gauge is not active yet")
def testClaimBAL():
    env = create_environment()
    testAccounts = TestAccounts()
    assert env.bal.balanceOf(env.treasuryManager) == 0
    env.sNOTE.claimBAL({"from": env.treasuryManager})
