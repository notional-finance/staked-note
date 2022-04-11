
pragma solidity =0.8.11;

interface IBalanceMinter {
    function mint(address gauge) external;
    function getBalancerToken() external returns (address);
}
