// SPDX-License-Identifier: MIT
pragma solidity =0.8.11;

import "../../interfaces/balancer/ILiquidityGauge.sol";

contract MockLiquidityGauge is ILiquidityGauge {
    uint256 public currentBalance;

    function deposit(uint256 _value, address _addr, bool _claim_rewards) external {
        currentBalance += _value;
    }

    function withdraw(uint256 _value, bool _claim_rewards) external {
        currentBalance -= _value;
    }
}
