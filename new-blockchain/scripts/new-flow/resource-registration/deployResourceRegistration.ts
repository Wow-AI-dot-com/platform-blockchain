import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { ethers, upgrades } from "hardhat";

const deployResourceRegistration = async (deployer: SignerWithAddress) => {
  const contract = await ethers.getContractFactory(
    "ResourceRegistration",
    deployer
  );
  const Contract = await contract.deploy();
  await Contract.deployed();
  console.log("ResourceRegistration 's address: ", Contract.address);

  return Contract;
};

export default deployResourceRegistration;
