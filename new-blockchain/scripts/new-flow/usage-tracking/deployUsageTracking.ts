import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { ethers, upgrades } from "hardhat";

const deployUsageTracking = async (
  deployer: SignerWithAddress,
  resourceRegistrationAddress: string,
  pricingAddress: string
) => {
  const contract = await ethers.getContractFactory("UsageTracking", deployer);
  const Contract = await contract.deploy(
    resourceRegistrationAddress,
    pricingAddress
  );
  await Contract.deployed();
  console.log("UsageTracking 's address: ", Contract.address);

  return Contract;
};

export default deployUsageTracking;
