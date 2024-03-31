import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { ethers, upgrades } from "hardhat";

const deployMarketplaceUpgradeable = async (deployer: SignerWithAddress) => {
  const upgradeableFactory = await ethers.getContractFactory(
    "Marketplace",
    deployer
  );
  const proxyInstance = await upgrades.deployProxy(upgradeableFactory);
  await proxyInstance.deployed();
  console.log("Marketplace proxy's address: ", proxyInstance.address);

  return proxyInstance;
};
export default deployMarketplaceUpgradeable;
