import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { ethers } from "hardhat";

const deployCaptcha88Upgradeable = async (deployer: SignerWithAddress) => {
  const upgradeableFactory = await ethers.getContractFactory(
    "Captcha",
    deployer
  );
  // const proxyInstance = await ethers.providers.de(upgradeableFactory);
  const UpgradeableFactory = await upgradeableFactory.deploy();
  await UpgradeableFactory.deployed();
  console.log("Captcha 's address: ", UpgradeableFactory.address);

  return UpgradeableFactory;
};

export default deployCaptcha88Upgradeable;
