// SPDX-License-Identifier: GPL-3.0-or-later
pragma solidity =0.8.11;

import "./utils/BoringOwnable.sol";
import "../interfaces/IDelegateRegistry.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract SnapshotDelegator is BoringOwnable {
    event DelegateUpdate(
        address indexed oldDelegate,
        address indexed newDelegate
    );
    event DelegateRegistryUpdated(
        address indexed oldRegistry,
        address indexed newRegistry
    );

    /// @notice the Gnosis delegate registry used by snapshot
    IDelegateRegistry public delegateRegistry;

    /// @notice the keccak encoded spaceId of the snapshot space
    bytes32 public spaceId;

    /// @notice the snapshot delegate for the deposit
    address public delegate;

    /// @notice Snapshot Delegator constructor
    /// @param _delegateRegistry delegate registry address
    /// @param _spaceId the id (or ENS name) of the snapshot space
    /// @param _initialDelegate address of the initial delegate
    constructor(
        IDelegateRegistry _delegateRegistry,
        bytes32 _spaceId,
        address _initialDelegate
    ) {
        delegateRegistry = _delegateRegistry;
        spaceId = _spaceId;
        _delegate(_initialDelegate);
    }

    /// @notice sets the snapshot space ID
    /// @param _spaceId space ID
    function setSpaceId(bytes32 _spaceId) external onlyOwner {
        delegateRegistry.clearDelegate(spaceId);
        spaceId = _spaceId;
        _delegate(delegate);
    }

    /// @notice sets the snapshot delegate
    /// @param newDelegate new delegate address
    function setDelegate(address newDelegate) external onlyOwner {
        _delegate(newDelegate);
    }

    /// @notice sets the delegate registry
    /// @param newRegistry new delegate registry
    function setDelegateRegistry(address newRegistry) external onlyOwner {
        address oldRegistry = address(delegateRegistry);
        delegateRegistry = IDelegateRegistry(newRegistry);
        emit DelegateRegistryUpdated(oldRegistry, newRegistry);
    }

    /// @notice clears the delegate from snapshot
    function clearDelegate() external onlyOwner {
        address oldDelegate = delegate;
        delegateRegistry.clearDelegate(spaceId);

        emit DelegateUpdate(oldDelegate, address(0));
    }

    function _delegate(address newDelegate) internal {
        address oldDelegate = delegate;
        delegateRegistry.setDelegate(spaceId, newDelegate);
        delegate = newDelegate;

        emit DelegateUpdate(oldDelegate, newDelegate);
    }
}
