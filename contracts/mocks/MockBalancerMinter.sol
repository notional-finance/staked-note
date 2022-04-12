// SPDX-License-Identifier: MIT
pragma solidity =0.8.11;

import "../../interfaces/balancer/IBalancerMinter.sol";

contract MockBalancerMinter is IBalancerMinter {
    address public currentGauge;
    address public balancerToken;

    constructor(address _balancerToken) {
        balancerToken = _balancerToken;
    }

    function mint(address gauge) external override {
        currentGauge = gauge;
    }

    function getBalancerToken() external override returns (address) {
        return balancerToken;
    }
}