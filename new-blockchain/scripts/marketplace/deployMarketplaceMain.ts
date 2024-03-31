import { ethers } from "hardhat";
import deployMarketplaceUpgradeable from "./deployMarketplace";

const deployMarketplaceUpgradeableMain = async () => {
  await deployMarketplaceUpgradeable((await ethers.getSigners())[0]);
};

deployMarketplaceUpgradeableMain();
