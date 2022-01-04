// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;
pragma abicoder v2;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

library EIP1271Wallet {
    uint256 internal constant ORDER_HASH_OFFSET = 36;
    bytes4 internal constant EIP1271_MAGIC_NUM = 0x20c13b0b;
    bytes4 internal constant EIP1271_INVALID_SIG = 0xffffffff;

    function extractOrderHash(bytes calldata encoded)
        internal
        pure
        returns (bytes32 orderHash)
    {
        require(
            encoded.length >= ORDER_HASH_OFFSET + 32,
            "encoded: invalid length"
        );
        return bytes32(encoded[ORDER_HASH_OFFSET:ORDER_HASH_OFFSET + 32]);
    }

    /**
     * @notice Verifies that the signer is the owner of the signing contract.
     */
    function isValidSignature(
        bytes calldata data,
        bytes calldata signature,
        address signer
    ) internal view returns (bytes4) {
        (address recovered, ECDSA.RecoverError error) = ECDSA.tryRecover(
            keccak256(
                abi.encodePacked(
                    "\x19Ethereum Signed Message:\n32",
                    extractOrderHash(data)
                )
            ),
            signature
        );
        if (error == ECDSA.RecoverError.NoError && recovered == signer) {
            return EIP1271_MAGIC_NUM;
        }
        return EIP1271_INVALID_SIG;
    }
}
