
pragma solidity =0.8.11;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IFeeDistributor {
    function claimTokens(address user, IERC20[] calldata tokens) external;
    function depositToken(IERC20 token, uint256 amount) external;
}
