import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { ethers, upgrades } from "hardhat";

const deployAxB = async (deployer: SignerWithAddress) => {
  const axbContract = await ethers.getContractFactory("AXBToken", deployer);
  const AxBContract = await axbContract.deploy(
    "AxB",
    "AXB",
    "100000000000000000000000000000000000000000000"
  );
  await AxBContract.deployed();
  console.log("AxB 's address: ", AxBContract.address);

  return AxBContract;
};

export default deployAxB;
