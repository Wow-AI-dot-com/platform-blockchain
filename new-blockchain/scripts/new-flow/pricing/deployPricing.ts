import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { ethers, upgrades } from "hardhat";

const deployPricing = async (
  deployer: SignerWithAddress,
  axbAddress: string,
  resourceRegistrationAddress: string,
) => {
  const contract = await ethers.getContractFactory("Pricing", deployer);
  const Contract = await contract.deploy(
    axbAddress,
    resourceRegistrationAddress,
  );
  await Contract.deployed();
  console.log("Pricing 's address: ", Contract.address);

  return Contract;
};

export default deployPricing;
