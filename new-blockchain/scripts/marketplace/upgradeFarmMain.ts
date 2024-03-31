import { ethers } from "hardhat";
import upgradeFarmUpgradeable from "./upgradeFarm";

const upgradeFarmUpgradeableMain = async (
  baseAddress: string,
  version: string = "FarmUpgradeable"
) => {
  await upgradeFarmUpgradeable(
    baseAddress,
    (
      await ethers.getSigners()
    )[0],
    version
  );
};

upgradeFarmUpgradeableMain("0x39499F78AA6eF5DF3C0Ed528a4928742a8e3812b"); // mainnet
