
pragma solidity =0.8.11;

interface ILiquidityGauge {
    function deposit(uint256 _value, address _addr, bool _claim_rewards) external;
    function withdraw(uint256 _value, bool _claim_rewards) external;
}
