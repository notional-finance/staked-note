// SPDX-License-Identifier: MIT
pragma solidity =0.8.11;

import "./MockERC20.sol";
import "../../interfaces/balancer/ILiquidityGauge.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MockLiquidityGauge is MockERC20, ILiquidityGauge {
    IERC20 public bptToken;

    constructor(IERC20 _bptToken) MockERC20("Mock BPT Gauge", "BPT-Gauge", 18, 0) {
        bptToken = _bptToken;
    }

    function deposit(
        uint256 _value,
        address _addr,
        bool _claim_rewards
    ) external {
        bptToken.transferFrom(_addr, address(this), _value);
        IERC20(address(this)).transfer(_addr, _value);
    }

    function withdraw(uint256 _value, bool _claim_rewards) external {
        _transfer(msg.sender, address(this), _value);
        bptToken.transfer(msg.sender, _value);
    }
}
