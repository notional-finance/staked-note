// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "../interfaces/notional/IStakedNote.sol";
import "./utils/BoringOwnable.sol";

abstract contract StakedNoteRef is BoringOwnable {
    IStakedNote public constant STAKED_NOTE =
        IStakedNote(0x38DE42F4BA8a35056b33A746A6b45bE9B1c3B9d2);
}
