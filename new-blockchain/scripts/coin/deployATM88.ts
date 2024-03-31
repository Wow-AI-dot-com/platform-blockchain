import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { ethers, upgrades } from "hardhat";

const deployATM88Upgradeable = async (deployer: SignerWithAddress) => {
  const upgradeableFactory = await ethers.getContractFactory(
    "ATM88",
    deployer
  );
  console.log('123123123123123')
  // const proxyInstance = await ethers.providers.de(upgradeableFactory);
  const UpgradeableFactory = await upgradeableFactory.deploy();
  await UpgradeableFactory.deployed()
  console.log("ATM88 's address: ", UpgradeableFactory.address);

  return UpgradeableFactory;
};

export default deployATM88Upgradeable;
