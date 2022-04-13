// SPDX-License-Identifier: MIT
pragma solidity =0.8.11;

import "../../interfaces/balancer/IBalancerMinter.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockBalancerMinter is IBalancerMinter {
    ERC20 public balancerToken;

    constructor(ERC20 _balancerToken) {
        balancerToken = _balancerToken;
    }

    function mint(address gauge) external override {
        balancerToken.transfer(msg.sender, 100e18);
    }

    function getBalancerToken() external override returns (address) {
        return address(balancerToken);
    }
}
