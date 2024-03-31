import { ethers } from "hardhat";
import deployATM88Upgradeable from "./deployATM88";

const deployATMUpgradeableMain = async () => {
  await deployATM88Upgradeable((await ethers.getSigners())[0]);
};

deployATMUpgradeableMain();
