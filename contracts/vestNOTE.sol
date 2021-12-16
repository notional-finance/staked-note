// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {BoringOwnable} from "./BoringOwnable.sol";

contract vestNOTE is ERC20, BoringOwnable, Initializable, UUPSUpgradeable {
    ERC20 public immutable stNOTE;
    NotionalProxy public immutable NOTIONAL;

    constructor(
        ERC20 _stNOTE,
        NotionalProxy _notional
    ) ERC20("Vested Staked NOTE", "vestNOTE") initializer { 
        stNOTE = _stNOTE;
        NOTIONAL = _notional;
    }

    function initialize(
        address _owner,
    ) external initializer {
        owner = _owner;
        emit OwnershipTransferred(address(0), _owner);
    }

    /// @notice vestNOTE transfers are disabled
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20) {
        revert("CANNOT TRANSFER");
    }

    // ERC-721 id:
    // address 20 bytes
    // 4 bytes for end time

    // function deposit()
    // function depositFor()
    // function createLock()
    // function increaseLockTime()
    // function withdraw()
    // function boostNToken()
    // function withdrawBoostedNToken()

    // TODO: do we need to know the historical vestNOTE voting power?
    // TODO: in order to do claims on boosted nToken you may need to know historical voting power / total voting power
    // at a particular epoch...
    // TODO: what if we model this as an ERC-721


    function _burn(address account, uint256 amount) internal override(ERC20) {
        // TODO: take into account burn penalty....

        // Handles event emission, balance update and total supply update
        ERC20._burn(account, amount);
    }

    function _mint(address account, uint256 amount) internal override(ERC20) {
        // Handles event emission, balance update and total supply update
        ERC20._mint(account, amount);
    }


}