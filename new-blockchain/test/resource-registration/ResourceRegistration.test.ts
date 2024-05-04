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

describe("ResourceRegistration", async () => {
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

  describe("Register single resource", async () => {
    it("Register single resource", async () => {
      const resourceType = "GPU";
      const provider = "AxB";
      const cpu = 12;
      const gpu = 12;
      const ram = 12;
      const disk = 1024;
      const pricePerHour = "5000000000000000000";
      const maxConcurrentSessions = 1;
      const tx = await ResourceRegistrationContract.connect(
        deployer
      ).registerResource(
        resourceType,
        provider,
        cpu,
        gpu,
        ram,
        disk,
        pricePerHour,
        maxConcurrentSessions
      );
      await tx.wait();
      const resourceList =
        await ResourceRegistrationContract.getResourceByAddress(
          deployer.address
        );
      assert(resourceList.length === 1);
    });
    it("Set availability of resource", async () => {
      const resourceType = "GPU";
      const provider = "AxB";
      const cpu = 12;
      const gpu = 12;
      const ram = 12;
      const disk = 1024;
      const pricePerHour = "5000000000000000000";
      const maxConcurrentSessions = 1;
      let tx = await ResourceRegistrationContract.connect(
        deployer
      ).registerResource(
        resourceType,
        provider,
        cpu,
        gpu,
        ram,
        disk,
        pricePerHour,
        maxConcurrentSessions
      );
      await tx.wait();

      const resourceList =
        await ResourceRegistrationContract.getResourceByAddress(
          deployer.address
        );
      assert(resourceList.length === 1);

      tx = await ResourceRegistrationContract.connect(
        deployer
      ).setResourceAvailability(0, true);

      const resource = await ResourceRegistrationContract.getResource(0);

      assert(resource?.available === true);
    });
  });

  describe("Register multi resource", async () => {
    it("Register multi resource", async () => {
      const resourceType = ["GPU", "GPU"];
      const provider = ["AxB", "GPU"];
      const cpu = [12, 12];
      const gpu = [12, 12];
      const ram = [12, 12];
      const disk = [1024, 12];
      const pricePerHour = ["5000000000000000000", "5000000000000000000"];
      const maxConcurrentSessions = [1, 1];
      const tx = await ResourceRegistrationContract.connect(
        deployer
      ).registerMultiResources(
        resourceType,
        provider,
        cpu,
        gpu,
        ram,
        disk,
        pricePerHour,
        maxConcurrentSessions
      );
      await tx.wait();
      const resourceList =
        await ResourceRegistrationContract.getResourceByAddress(
          deployer.address
        );
      assert(resourceList.length === 2);
    });
  });
});
