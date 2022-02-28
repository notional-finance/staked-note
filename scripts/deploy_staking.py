from brownie import accounts, network

from scripts.deployers.snote_deployer import SNoteDeployer
from scripts.deployers.treasury_manager_deployer import TreasuryManagerDeployer
from scripts.deployers.balancer_deployer import BalancerDeployer

#   def deployBalancer(deployer):
    #balancer = BalancerDeployer(network.show_active(), deployer)
    #balancer.deployNotePool()

#def deploySNote(deployer):
#    snote = SNoteDeployer(network.show_active(), deployer)
#    snote.deploy()

#def deployTreasuryManager(deployer):
#    manager = TreasuryManagerDeployer(network.show_active(), deployer)
#    manager.deploy()

def main():
    deployer = accounts.load(network.show_active().upper() + "_DEPLOYER")
    snote = SNoteDeployer(network.show_active(), deployer)
    snote.deployEmptyProxy()

#    deploySNote(deployer)
#    deployTreasuryManager(deployer)
#    deployBalancer(deployer)
