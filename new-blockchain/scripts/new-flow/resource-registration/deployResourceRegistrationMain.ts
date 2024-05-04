import { ethers } from "hardhat";
import deployResourceRegistration from "./deployResourceRegistration";

const deployResourceRegistrationMain = async () => {
  await deployResourceRegistration((await ethers.getSigners())[0]);
};

deployResourceRegistrationMain();
