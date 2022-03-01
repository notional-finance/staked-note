from brownie import accounts, network

from scripts.deployers.snote_deployer import SNoteDeployer
from scripts.deployers.treasury_manager_deployer import TreasuryManagerDeployer
from scripts.deployers.balancer_deployer import BalancerDeployer
from scripts.initializers.balancer_initializer import BalancerInitializer

def initBalancer(deployer):
    init = BalancerInitializer(network.show_active(), deployer)
    init.initPool()

def deployEmptyProxy(deployer):
    snote = SNoteDeployer(network.show_active(), deployer)
    snote.deployEmptyProxy()

def deployBalancerPool(deployer):
    balancer = BalancerDeployer(network.show_active(), deployer)
    balancer.deployNotePool()

def upgradeSNote(deployer):
    snote = SNoteDeployer(network.show_active(), deployer)
    snote.upgradeSNote()

def deployTreasuryManager(deployer):
    manager = TreasuryManagerDeployer(network.show_active(), deployer)
    manager.deploy()

def main():
    deployer = accounts.load(network.show_active().upper() + "_DEPLOYER")
    deployEmptyProxy(deployer)
    deployBalancerPool(deployer)
    upgradeSNote(deployer)
    initBalancer(deployer)
    deployTreasuryManager(deployer)
