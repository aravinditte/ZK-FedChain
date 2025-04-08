// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;

import "@openzeppelin/contracts/access/Ownable.sol";
import "../interfaces/IZKVerifier.sol";

contract ZKVerifier is Ownable, IZKVerifier {
    bytes public gradientVerificationKey;
    bytes public trainingVerificationKey;
    
    event VerificationKeysUpdated(string circuitType);
    
    constructor(bytes memory _gradientVerificationKey, bytes memory _trainingVerificationKey) {
        gradientVerificationKey = _gradientVerificationKey;
        trainingVerificationKey = _trainingVerificationKey;
    }
    
    function updateVerificationKeys(string memory circuitType, bytes memory newKey) external onlyOwner {
        if (keccak256(abi.encodePacked(circuitType)) == keccak256(abi.encodePacked("gradient"))) {
            gradientVerificationKey = newKey;
        } else if (keccak256(abi.encodePacked(circuitType)) == keccak256(abi.encodePacked("training"))) {
            trainingVerificationKey = newKey;
        } else {
            revert("Invalid circuit type");
        }
        emit VerificationKeysUpdated(circuitType);
    }
    
    function verifyGradientProof(
        bytes memory proof,
        bytes memory publicInputs
    ) external view override returns (bool) {
        return _simulateVerification(proof, publicInputs, gradientVerificationKey);
    }
    
    function verifyTrainingProof(
        bytes memory proof,
        bytes memory publicInputs
    ) external view override returns (bool) {
        return _simulateVerification(proof, publicInputs, trainingVerificationKey);
    }
    
    function _simulateVerification(
        bytes memory proof,
        bytes memory publicInputs,
        bytes memory verificationKey
    ) internal pure returns (bool) {
        return proof.length > 0 && publicInputs.length > 0 && verificationKey.length > 0;
    }
}
