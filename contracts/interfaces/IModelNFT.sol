// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

interface IModelNFT {
    function mintModel(
        address owner,
        string memory ipfsHash,
        uint256 version,
        uint256 accuracy,
        string memory metadataURI
    ) external returns (uint256);

    function getModelMetadata(uint256 tokenId)
        external
        view
        returns (
            string memory ipfsHash,
            uint256 version,
            uint256 accuracy,
            uint256 timestamp
        );
}
