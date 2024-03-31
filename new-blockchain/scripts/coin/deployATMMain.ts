import { ethers } from "hardhat";
import deployATMUpgradeable from "./deployATM";

const deployATMUpgradeableMain = async () => {
  await deployATMUpgradeable((await ethers.getSigners())[0]);
};

deployATMUpgradeableMain();
