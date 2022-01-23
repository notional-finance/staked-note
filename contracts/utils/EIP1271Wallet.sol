// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;
pragma abicoder v2;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {WETH9} from "interfaces/WETH9.sol";

contract EIP1271Wallet {
    /// 0x order encoding
    /// offset       field
    /// 0            IEIP1271Data(address(0)).OrderWithHash.selector (4)
    /// 36           orderHash (32)
    /// 68           makerAddress (32)
    /// 100          takerAddress (32)
    /// 132          feeRecipient (32)
    /// 164          senderAddress (32)
    /// 196          makerAmount (32)
    /// 228          takerAmount (32)
    /// 260          makerFee (32)
    /// 292          takerFee (32)
    /// 324          expiration (32)
    /// 356          salt (32)
    /// 388          (32)
    /// 420          (32)
    /// 452          (32)
    /// 484          (32)
    /// 516          (32)
    /// 548          makerAssetData selector (4)
    /// 552          makerAssetToken (32)
    /// 584          (32)
    /// 616          (28)
    /// 644          takerAssetData selector (4)
    /// 648          takerAssetToken (32)
    uint256 internal constant ORDER_HASH_OFFSET = 36;
    uint256 internal constant FEE_RECIPIENT_OFFSET = 132;
    uint256 internal constant MAKER_AMOUNT_OFFSET = 196;
    uint256 internal constant TAKER_AMOUNT_OFFSET = 228;
    uint256 internal constant MAKER_TOKEN_OFFSET = 552;
    uint256 internal constant TAKER_TOKEN_OFFSET = 648;

    bytes4 internal constant EIP1271_MAGIC_NUM = 0x20c13b0b;
    bytes4 internal constant EIP1271_INVALID_SIG = 0xffffffff;
    WETH9 public immutable WETH;
    mapping(address => address) public priceOracles;
    mapping(address => uint256) public slippageLimits;

    constructor(WETH9 _weth) {
        WETH = _weth;
    }

    function toAddress(bytes memory _bytes, uint256 _start)
        private
        pure
        returns (address)
    {
        // _bytes.length checked by the caller
        address tempAddress;

        assembly {
            tempAddress := div(
                mload(add(add(_bytes, 0x20), _start)),
                0x1000000000000000000000000
            )
        }

        return tempAddress;
    }

    function toUint256(bytes memory _bytes, uint256 _start)
        private
        pure
        returns (uint256)
    {
        // _bytes.length checked by the caller
        uint256 tempUint;

        assembly {
            tempUint := mload(add(add(_bytes, 0x20), _start))
        }

        return tempUint;
    }

    function toBytes32(bytes memory _bytes, uint256 _start)
        private
        pure
        returns (bytes32)
    {
        // _bytes.length checked by the caller
        bytes32 tempBytes32;

        assembly {
            tempBytes32 := mload(add(add(_bytes, 0x20), _start))
        }

        return tempBytes32;
    }

    function extractOrderInfo(bytes memory encoded)
        public
        pure
        returns (
            address makerToken,
            address takerToken,
            address feeRecipient,
            uint256 makerAmount,
            uint256 takerAmount
        )
    {
        require(
            encoded.length >= TAKER_TOKEN_OFFSET + 32,
            "encoded: invalid length"
        );
        makerToken = toAddress(encoded, MAKER_TOKEN_OFFSET + 12);
        takerToken = toAddress(encoded, TAKER_TOKEN_OFFSET + 12);
        feeRecipient = toAddress(encoded, FEE_RECIPIENT_OFFSET + 12);
        makerAmount = toUint256(encoded, MAKER_AMOUNT_OFFSET);
        takerAmount = toUint256(encoded, TAKER_AMOUNT_OFFSET);
    }

    function extractOrderHash(bytes memory encoded)
        public
        pure
        returns (bytes32)
    {
        require(
            encoded.length >= ORDER_HASH_OFFSET + 32,
            "encoded: invalid length"
        );

        return toBytes32(encoded, ORDER_HASH_OFFSET);
    }

    function isValidOrder(bytes memory order) internal view returns (bool) {
        (
            address makerToken,
            address takerToken,
            address feeRecipient,
            uint256 makerAmount,
            uint256 takerAmount
        ) = extractOrderInfo(order);

        // No fee recipient allowed
        if (feeRecipient != address(0)) return false;

        // TakerToken (proceeds) should always be WETH
        if (takerToken != address(WETH)) return false;

        address priceOracle = priceOracles[makerToken];

        // Price oracle not defined
        if (priceOracle == address(0)) return false;

        uint256 slippageLimit = slippageLimits[makerToken];

        // Slippage limit not defined
        if (slippageLimit == 0) return false;

        return true;
    }

    /**
     * @notice Verifies that the signer is the owner of the signing contract.
     */
    function isValidSignature(
        bytes calldata data,
        bytes calldata signature,
        address signer
    ) internal view returns (bytes4) {
        if (!isValidOrder(data)) return EIP1271_INVALID_SIG;

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
