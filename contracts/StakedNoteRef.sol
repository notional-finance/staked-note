// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "../interfaces/notional/IStakedNote.sol";

abstract contract StakedNoteRef {
    IStakedNote public constant STAKED_NOTE =
        IStakedNote(0x38DE42F4BA8a35056b33A746A6b45bE9B1c3B9d2);

    /// @notice Only allows the `owner` to execute the function.
    modifier onlyOwner() {
        require(msg.sender == STAKED_NOTE.owner(), "Caller is not the owner");
        _;
    }
}
