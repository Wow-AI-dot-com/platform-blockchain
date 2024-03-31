import { ethers } from "hardhat";
import deployCaptchaUpgradeable from "./deployCaptcha";

const deployCaptchaUpgradeableMain = async () => {
  await deployCaptchaUpgradeable((await ethers.getSigners())[0]);
};

deployCaptchaUpgradeableMain();
