import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { ethers, upgrades } from "hardhat";

const upgradeFarmUpgradeable = async (
  baseAddress: string,
  deployer: SignerWithAddress,
  version: string = "FarmUpgradeable"
) => {
  const FarmUpgradeableFactory = await ethers.getContractFactory(
    version,
    deployer
  );
  const FarmUpgradeableInstance = await upgrades.upgradeProxy(
    baseAddress,
    FarmUpgradeableFactory
  );
  console.log("FarmUpgradeable upgraded");

  return FarmUpgradeableInstance;
};

export default upgradeFarmUpgradeable;
