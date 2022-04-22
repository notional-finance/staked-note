// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

interface ILiquidityGaugeController {
    function vote_for_gauge_weights(address gauge_addr, uint256 user_weight)
        external;

    function last_user_vote(address user, address gauge)
        external
        view
        returns (uint256);

    function vote_user_power(address user) external view returns (uint256);

    function gauge_types(address gauge) external view returns (int128);
}
