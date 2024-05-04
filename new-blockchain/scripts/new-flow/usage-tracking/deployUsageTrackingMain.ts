import { ethers } from "hardhat";
import deployUsageTracking from "./deployUsageTracking";

const pricingAddress = "";
const resourceRegistrationAddress = "";

const deployUsageTrackingMain = async () => {
  await deployUsageTracking(
    (
      await ethers.getSigners()
    )[0],
    pricingAddress,
    resourceRegistrationAddress
  );
};

deployUsageTrackingMain();
