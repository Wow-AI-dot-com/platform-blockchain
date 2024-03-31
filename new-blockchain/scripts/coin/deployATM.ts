import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { ethers, upgrades } from "hardhat";

const deployATMUpgradeable = async (deployer: SignerWithAddress) => {
  const upgradeableFactory = await ethers.getContractFactory(
    "ATMUpgradeable",
    deployer
  );
  const proxyInstance = await upgrades.deployProxy(upgradeableFactory);
  await proxyInstance.deployed();
  console.log("ATMUpgradeable proxy's address: ", proxyInstance.address);

  return proxyInstance;
};

export default deployATMUpgradeable;
