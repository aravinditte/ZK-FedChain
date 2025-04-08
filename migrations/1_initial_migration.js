const FedToken = artifacts.require("tokens/FedToken");
const ModelNFT = artifacts.require("tokens/ModelNFT");
const ZKVerifier = artifacts.require("core/ZKVerifier");
const FedChainCore = artifacts.require("core/FedChainCore");

module.exports = async function (deployer, network, accounts) {
  const admin = accounts[0];
  
  // Deploy FedToken
  await deployer.deploy(FedToken);
  const fedToken = await FedToken.deployed();
  console.log(`FedToken deployed at: ${fedToken.address}`);
  
  // Deploy ModelNFT
  await deployer.deploy(ModelNFT);
  const modelNFT = await ModelNFT.deployed();
  console.log(`ModelNFT deployed at: ${modelNFT.address}`);
  
  // Deploy ZKVerifier with dummy verification keys
  const gradientVerificationKey = "0x1234";
  const trainingVerificationKey = "0x5678";
  await deployer.deploy(ZKVerifier, gradientVerificationKey, trainingVerificationKey);
  const zkVerifier = await ZKVerifier.deployed();
  console.log(`ZKVerifier deployed at: ${zkVerifier.address}`);
  
  // Deploy FedChainCore with initial model hash
  const initialModelIpfsHash = "QmInitialModelHash";
  await deployer.deploy(
    FedChainCore,
    fedToken.address,
    modelNFT.address,
    zkVerifier.address,
    initialModelIpfsHash
  );
  const fedChainCore = await FedChainCore.deployed();
  console.log(`FedChainCore deployed at: ${fedChainCore.address}`);
  
  // Transfer ownership of token contracts to FedChainCore
  await fedToken.transferOwnership(fedChainCore.address);
  await modelNFT.transferOwnership(fedChainCore.address);
  
  console.log("Contract deployment and setup complete!");
};
