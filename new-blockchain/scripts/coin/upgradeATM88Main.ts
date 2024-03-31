import { ethers } from "hardhat";
import upgradeGameUpgradeable from "./upgradeATM88";

const upgradeGameUpgradeableMain = async (
  baseAddress: string,
  version: string = "ATM88Upgradeable"
) => {
  await upgradeGameUpgradeable(
    baseAddress,
    (
      await ethers.getSigners()
    )[0],
    version
  );
};

upgradeGameUpgradeableMain("0xbc0640a9AF9048385A241b899Bb5184796ae0C98"); // mainnet
