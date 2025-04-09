// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "../interfaces/IModelNFT.sol";

contract ModelNFT is ERC721URIStorage, Ownable, IModelNFT {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;
    
    struct ModelMetadata {
        string ipfsHash;
        uint256 version;
        uint256 accuracy;
        uint256 timestamp;
    }
    
    mapping(uint256 => ModelMetadata) public models;
    
    constructor() ERC721("FedChain Model", "FCM") {}
    
    function mintModel(
        address owner,
        string memory ipfsHash,
        uint256 version,
        uint256 accuracy,
        string memory metadataURI
    ) external override onlyOwner returns (uint256) {
        _tokenIds.increment();
        uint256 newModelId = _tokenIds.current();
        
        _mint(owner, newModelId);
        _setTokenURI(newModelId, metadataURI);
        
        models[newModelId] = ModelMetadata({
            ipfsHash: ipfsHash,
            version: version,
            accuracy: accuracy,
            timestamp: block.timestamp
        });
        
        return newModelId;
    }
    
    function getModelMetadata(uint256 tokenId) external override view returns (
        string memory ipfsHash,
        uint256 version,
        uint256 accuracy,
        uint256 timestamp
    ) {
        require(_exists(tokenId), "Model does not exist");
        ModelMetadata memory metadata = models[tokenId];
        return (
            metadata.ipfsHash,
            metadata.version,
            metadata.accuracy,
            metadata.timestamp
        );
    }
}
