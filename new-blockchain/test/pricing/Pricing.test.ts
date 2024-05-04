import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { assert, expect } from "chai";
import { Contract } from "ethers";
import { ethers } from "hardhat";
import deployAxB from "../../scripts/new-flow/axb/deployAxB";
import deployResourceRegistration from "../../scripts/new-flow/resource-registration/deployResourceRegistration";
import deployPricing from "../../scripts/new-flow/pricing/deployPricing";
import deployUsageTrackingContract from "../../scripts/new-flow/usage-tracking/deployUsageTracking";

let deployer: SignerWithAddress;
let user: SignerWithAddress;
let AxBContract: Contract;
let ResourceRegistrationContract: Contract;
let PricingContract: Contract;
let UsageTrackingContract: Contract;

describe("Pricing", async () => {
  beforeEach(async () => {
    [deployer, user] = await ethers.getSigners();
    AxBContract = await deployAxB(deployer);
    ResourceRegistrationContract = await deployResourceRegistration(deployer);
    PricingContract = await deployPricing(
      deployer,
      AxBContract.address,
      ResourceRegistrationContract.address
    );
    UsageTrackingContract = await deployUsageTrackingContract(
      deployer,
      ResourceRegistrationContract.address,
      PricingContract.address
    );
  });

  describe("Deposit", async () => {
    it("Deposit", async () => {
      const amount = "1000000000000000000";
      let tx = await AxBContract.connect(deployer).approve(
        PricingContract.address,
        amount
      );
      tx = await PricingContract.connect(deployer).depositTokens(amount);
      await tx.wait();
      const balance = await PricingContract.userBalances(deployer.address);
      assert.equal(balance.toString(), amount);
    });
  });

  describe("Withdraw", async () => {
    it("Withdraw", async () => {
      const amount = "1000000000000000000";
      let tx = await AxBContract.connect(deployer).approve(
        PricingContract.address,
        amount
      );
      tx = await PricingContract.connect(deployer).depositTokens(amount);
      await tx.wait();
      let balance = await PricingContract.userBalances(deployer.address);
      assert.equal(balance.toString(), amount);

      tx = await PricingContract.connect(deployer).withdrawTokens(amount);
      balance = await PricingContract.userBalances(deployer.address);
      assert.equal(balance.toString(), "0");
    });
  });
});
