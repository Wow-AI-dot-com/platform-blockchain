/* eslint-disable node/no-unpublished-import */
import { ethers } from "hardhat";

export const hashMessage = (types: Array<string>, data: Array<any>) => {
  return ethers.utils.solidityKeccak256(types, data);
};
