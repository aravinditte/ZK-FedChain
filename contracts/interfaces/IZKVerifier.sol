// SPDX-License-Identifier: MIT
pragma solidity 0.8.17;

interface IZKVerifier {
    function verifyGradientProof(bytes memory proof, bytes memory publicInputs) external view returns (bool);
    function verifyTrainingProof(bytes memory proof, bytes memory publicInputs) external view returns (bool);
}
