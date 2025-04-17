const FedToken = artifacts.require("FedToken");
const ModelNFT = artifacts.require("ModelNFT");
const ZKVerifier = artifacts.require("ZKVerifier");
const FedChainCore = artifacts.require("FedChainCore");

module.exports = async function (deployer) {
  // Deploy contracts in proper order
  await deployer.deploy(FedToken);
  await deployer.deploy(ModelNFT);
  
  // Deploy ZKVerifier with dummy keys
  const gradientKey = web3.utils.asciiToHex("gradient-dummy-key");
  const trainingKey = web3.utils.asciiToHex("training-dummy-key");
  await deployer.deploy(ZKVerifier, gradientKey, trainingKey);

  // Get deployed instances
  const fedToken = await FedToken.deployed();
  const modelNFT = await ModelNFT.deployed();
  const zkVerifier = await ZKVerifier.deployed();

  // Deploy FedChainCore with initial parameters
  await deployer.deploy(
    FedChainCore,
    fedToken.address,
    modelNFT.address,
    zkVerifier.address,
    "QmInitialModelHash" // Initial model IPFS hash
  );

  // Transfer ownership of token contracts
  const fedChainCore = await FedChainCore.deployed();
  await fedToken.transferOwnership(fedChainCore.address);
  await modelNFT.transferOwnership(fedChainCore.address);
};
