import { ethers } from "hardhat";
import deployAxB from "./deployAxB";

const deployAxBMain = async () => {
  await deployAxB((await ethers.getSigners())[0]);
};

deployAxBMain();
