// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "../interfaces/notional/IStakedNote.sol";

abstract contract StakedNoteRef {
    IStakedNote public constant STAKED_NOTE =
        IStakedNote(0x1344A36A1B56144C3Bc62E7757377D288fDE0369);

    /// @notice Only allows the `owner` to execute the function.
    modifier onlyOwner() {
        require(msg.sender == STAKED_NOTE.owner(), "Caller is not the owner");
        _;
    }
}
