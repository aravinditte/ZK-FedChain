// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "../interfaces/IFedToken.sol";
import "../interfaces/IModelNFT.sol";
import "../interfaces/IZKVerifier.sol";

contract FedChainCore is Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    
    // Contract state variables
    IFedToken public fedToken;
    IModelNFT public modelNFT;
    IZKVerifier public zkVerifier;
    
    Counters.Counter public roundId;
    uint256 public roundDuration = 5 minutes;
    uint256 public minParticipants = 1;
    uint256 public stakingAmount = 100 * 10**18;
    
    string public currentModelIpfsHash;
    uint256 public currentModelVersion;
    
    // Participant structure and mapping
    struct Participant {
        bool isRegistered;
        uint256 stakedAmount;
        uint256 totalRewards;
        uint256 lastActiveRound;
    }
    mapping(address => Participant) public participants;
    
    // Round structure and mappings
    struct Round {
        uint256 startTime;
        uint256 endTime;
        bool finalized;
        string resultModelIpfsHash;
        uint256 participantCount;
        mapping(address => bool) hasSubmitted;
        mapping(address => string) gradientHashes;
        mapping(address => uint256) rewards;
    }
    mapping(uint256 => Round) public rounds;
    mapping(uint256 => address[]) public roundParticipants;
    
    // Event declarations
    event ParticipantRegistered(address indexed participant, uint256 stakedAmount);
    event RoundStarted(uint256 indexed roundId, uint256 startTime, uint256 endTime);
    event GradientSubmitted(uint256 indexed roundId, address indexed participant, string gradientIpfsHash);
    event RoundFinalized(uint256 indexed roundId, string resultModelIpfsHash, uint256 modelVersion);
    event ModelMinted(uint256 indexed tokenId, uint256 version, string ipfsHash);
    event RewardDistributed(uint256 indexed roundId, address indexed participant, uint256 amount);

    constructor(
        address _fedTokenAddress,
        address _modelNFTAddress,
        address _zkVerifierAddress,
        string memory _initialModelIpfsHash
    ) {
        fedToken = IFedToken(_fedTokenAddress);
        modelNFT = IModelNFT(_modelNFTAddress);
        zkVerifier = IZKVerifier(_zkVerifierAddress);
        
        currentModelIpfsHash = _initialModelIpfsHash;
        currentModelVersion = 1;
        
        roundId.increment();
        uint256 currentRoundId = roundId.current();
        rounds[currentRoundId].startTime = block.timestamp;
        rounds[currentRoundId].endTime = block.timestamp + roundDuration;
        
        emit RoundStarted(currentRoundId, block.timestamp, block.timestamp + roundDuration);
    }

    function register() external nonReentrant {
        require(!participants[msg.sender].isRegistered, "Already registered");
        require(fedToken.transferFrom(msg.sender, address(this), stakingAmount), "Staking failed");
        
        participants[msg.sender] = Participant({
            isRegistered: true,
            stakedAmount: stakingAmount,
            totalRewards: 0,
            lastActiveRound: 0
        });
        
        emit ParticipantRegistered(msg.sender, stakingAmount);
    }


    function submitGradient(
        uint256 _roundId,
        string memory _gradientIpfsHash,
        bytes memory _zkProof,
        bytes memory _publicInputs
    ) external nonReentrant {
        require(participants[msg.sender].isRegistered, "Not registered");
        require(_roundId == roundId.current(), "Invalid round");
        require(block.timestamp <= rounds[_roundId].endTime, "Round ended");
        require(!rounds[_roundId].hasSubmitted[msg.sender], "Already submitted");
        
        require(zkVerifier.verifyGradientProof(_zkProof, _publicInputs), "Invalid ZK proof");
        
        rounds[_roundId].hasSubmitted[msg.sender] = true;
        rounds[_roundId].gradientHashes[msg.sender] = _gradientIpfsHash;
        rounds[_roundId].participantCount++;
        roundParticipants[_roundId].push(msg.sender);
        
        participants[msg.sender].lastActiveRound = _roundId;
        
        emit GradientSubmitted(_roundId, msg.sender, _gradientIpfsHash);
        
        // Auto-finalize if minimum participants reached
        if (rounds[_roundId].participantCount >= minParticipants) {
            _finalizeRound(_roundId);
        }
    }


    function finalizeRound(uint256 _roundId) external onlyOwner {
        require(_roundId == roundId.current(), "Invalid round");
        require(block.timestamp > rounds[_roundId].endTime, "Round not ended");
        require(!rounds[_roundId].finalized, "Already finalized");
        require(rounds[_roundId].participantCount >= minParticipants, "Not enough participants");
        
        _finalizeRound(_roundId);
    }

    function _finalizeRound(uint256 _roundId) internal {
        currentModelVersion++;
        
        roundId.increment();
        uint256 newRoundId = roundId.current();
        rounds[newRoundId].startTime = block.timestamp;
        rounds[newRoundId].endTime = block.timestamp + roundDuration;
        
        emit RoundStarted(newRoundId, block.timestamp, block.timestamp + roundDuration);
        
        rounds[_roundId].finalized = true;
        emit RoundFinalized(_roundId, currentModelIpfsHash, currentModelVersion);
    }

    function updateModel(
        uint256 _roundId,
        string memory _newModelIpfsHash,
        uint256 _accuracy,
        string memory _metadataURI,
        bytes memory _zkProof,
        bytes memory _publicInputs
    ) external onlyOwner {
        require(rounds[_roundId].finalized, "Round not finalized");
        require(bytes(rounds[_roundId].resultModelIpfsHash).length == 0, "Model already updated");
        
        require(zkVerifier.verifyTrainingProof(_zkProof, _publicInputs), "Invalid aggregation proof");
        
        currentModelIpfsHash = _newModelIpfsHash;
        rounds[_roundId].resultModelIpfsHash = _newModelIpfsHash;
        
        uint256 tokenId = modelNFT.mintModel(
            address(this),
            _newModelIpfsHash,
            currentModelVersion,
            _accuracy,
            _metadataURI
        );
        
        emit ModelMinted(tokenId, currentModelVersion, _newModelIpfsHash);
    }

    function distributeRewards(uint256 _roundId, address[] memory _participants, uint256[] memory _rewards) external onlyOwner {
        require(rounds[_roundId].finalized, "Round not finalized");
        require(_participants.length == _rewards.length, "Arrays length mismatch");
        
        for (uint256 i = 0; i < _participants.length; i++) {
            address participant = _participants[i];
            uint256 reward = _rewards[i];
            
            require(rounds[_roundId].hasSubmitted[participant], "Participant did not submit");
            require(rounds[_roundId].rewards[participant] == 0, "Rewards already distributed");
            
            rounds[_roundId].rewards[participant] = reward;
            participants[participant].totalRewards += reward;
            
            fedToken.mint(participant, reward);
            emit RewardDistributed(_roundId, participant, reward);
        }
    }

    function getRoundParticipants(uint256 _roundId) external view returns (address[] memory) {
        return roundParticipants[_roundId];
    }

    function getParticipantReward(uint256 _roundId, address _participant) external view returns (uint256) {
        return rounds[_roundId].rewards[_participant];
    }
}
