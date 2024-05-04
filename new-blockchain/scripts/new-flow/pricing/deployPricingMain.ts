import { ethers } from "hardhat";
import deployPricing from "./deployPricing";

const axbAddress = "";
const resourceRegistrationAddress = "";

const deployPricingMain = async () => {
  await deployPricing(
    (
      await ethers.getSigners()
    )[0],
    axbAddress,
    resourceRegistrationAddress
  );
};

deployPricingMain();
