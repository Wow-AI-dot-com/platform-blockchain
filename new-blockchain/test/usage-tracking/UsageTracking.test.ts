import { SignerWithAddress } from "@nomiclabs/hardhat-ethers/signers";
import { assert, expect } from "chai";
import { Contract } from "ethers";
import { ethers } from "hardhat";
import deployAxB from "../../scripts/new-flow/axb/deployAxB";
import deployResourceRegistration from "../../scripts/new-flow/resource-registration/deployResourceRegistration";
import deployPricing from "../../scripts/new-flow/pricing/deployPricing";
import deployUsageTrackingContract from "../../scripts/new-flow/usage-tracking/deployUsageTracking";

let deployer: SignerWithAddress;
let lessor: SignerWithAddress;
let AxBContract: Contract;
let ResourceRegistrationContract: Contract;
let PricingContract: Contract;
let UsageTrackingContract: Contract;

describe("UsageTracking", async () => {
  beforeEach(async () => {
    [deployer, lessor] = await ethers.getSigners();
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

    let tx = await AxBContract.connect(deployer).approve(
      PricingContract.address,
      ethers.utils.parseEther("1000")
    );
    await tx.wait();
    tx = await PricingContract.connect(deployer).depositTokens(
      ethers.utils.parseEther("1000")
    );
    await tx.wait();
    tx = await PricingContract.connect(deployer).setUsageContractAddress(
      UsageTrackingContract.address
    );
    await tx.wait();
  });

  const registerResource = async () => {
    const resourceType = "GPU";
    const provider = "AxB";
    const cpu = 12;
    const gpu = 12;
    const ram = 12;
    const disk = 1024;
    const pricePerHour = ethers.utils.parseEther("1");
    const maxConcurrentSessions = 1;
    let tx = await ResourceRegistrationContract.connect(
      lessor
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
      await ResourceRegistrationContract.getResourceByAddress(lessor.address);
  };

  const registerMultiResource = async () => {
    const resourceType = ["GPU", "GPU"];
    const provider = ["AxB", "GPU"];
    const cpu = [12, 12];
    const gpu = [12, 12];
    const ram = [12, 12];
    const disk = [1024, 12];
    const pricePerHour = [
      ethers.utils.parseEther("1"),
      ethers.utils.parseEther("1"),
    ];
    const maxConcurrentSessions = [1, 1];
    const tx = await ResourceRegistrationContract.connect(
      lessor
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
      await ResourceRegistrationContract.getResourceByAddress(lessor.address);
    assert(resourceList.length === 2);
  };

  describe("Start single session", async () => {
    it("Start single session", async () => {
      await registerResource();

      const tx = await UsageTrackingContract.connect(deployer).startSession(
        0,
        10
      );

      const sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      assert(sessionData.length === 1);
    });

    it("Start single session and end session", async () => {
      await registerResource();

      let tx = await UsageTrackingContract.connect(deployer).startSession(
        0,
        10
      );
      await tx.wait();

      const sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      assert(sessionData.length === 1);
      await ethers.provider.send("evm_increaseTime", [3600]); // Increase time by 1 hour
      tx = await UsageTrackingContract.connect(deployer).endSession(0);
      await tx.wait();

      const lessorBalance = await PricingContract.userBalances(lessor.address);

      assert(
        lessorBalance.toString() === ethers.utils.parseEther("1").toString()
      );
    });

    it("Start single session, end session and withdraw", async () => {
      await registerResource();

      let tx = await UsageTrackingContract.connect(deployer).startSession(
        0,
        10
      );
      await tx.wait();

      const sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      assert(sessionData.length === 1);
      await ethers.provider.send("evm_increaseTime", [3600]); // Increase time by 1 hour
      tx = await UsageTrackingContract.connect(deployer).endSession(0);
      await tx.wait();

      const lessorBalance = await PricingContract.userBalances(lessor.address);

      assert(
        lessorBalance.toString() === ethers.utils.parseEther("1").toString()
      );

      tx = await PricingContract.connect(lessor).withdrawTokens(lessorBalance);
      await tx.wait();

      const axbBalance = await AxBContract.balanceOf(lessor.address);
      assert(axbBalance.toString() === lessorBalance.toString());
    });

    it("Start single session, end session multi times", async () => {
      await registerResource();
      await registerResource();

      let tx = await UsageTrackingContract.connect(deployer).startSession(
        0,
        10
      );
      await tx.wait();

      let sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      assert(sessionData.length === 1);
      await ethers.provider.send("evm_increaseTime", [3600]); // Increase time by 1 hour

      tx = await UsageTrackingContract.connect(deployer).startSession(1, 10);
      await tx.wait();

      sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      assert(sessionData.length === 2);
      await ethers.provider.send("evm_increaseTime", [3600]); // Increase time by 1 hour
      for (const data of sessionData) {
        tx = await UsageTrackingContract.connect(deployer).endSession(data);
        await tx.wait();
      }

      tx = await UsageTrackingContract.connect(deployer).startSession(0, 10);
      await tx.wait();

      tx = await UsageTrackingContract.connect(deployer).startSession(1, 10);
      await tx.wait();
      await ethers.provider.send("evm_increaseTime", [3600]); // Increase time by 1 hour

      sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      for (const data of sessionData) {
        tx = await UsageTrackingContract.connect(deployer).endSession(data);
        await tx.wait();
      }

      tx = await UsageTrackingContract.connect(deployer).startSession(0, 10);
      await tx.wait();

      tx = await UsageTrackingContract.connect(deployer).startSession(1, 10);
      await tx.wait();
      await ethers.provider.send("evm_increaseTime", [3600]); // Increase time by 1 hour

      sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      for (const data of sessionData) {
        tx = await UsageTrackingContract.connect(deployer).endSession(data);
        await tx.wait();
      }
    });

    it("Not owner end session ", async () => {
      await registerResource();

      let tx = await UsageTrackingContract.connect(deployer).startSession(
        0,
        10
      );
      await tx.wait();

      const sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      assert(sessionData.length === 1);
      await ethers.provider.send("evm_increaseTime", [3600]); // Increase time by 1 hour
      try {
        tx = await UsageTrackingContract.connect(lessor).endSession(0);
        await tx.wait();
      } catch (error: any) {
        assert(error.message.includes("Only the session initiator can end it"));
      }
    });
  });

  describe("Start multi session", async () => {
    it("Start multi session", async () => {
      await registerMultiResource();
      const resourceIds = [0, 1];
      const estimateHours = [10, 10];

      const tx = await UsageTrackingContract.connect(
        deployer
      ).startMultiSessions(resourceIds, estimateHours);
      await tx.wait();

      const sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      assert(sessionData.length === 2);
    });

    it("Start multi session and end multi session", async () => {
      await registerMultiResource();
      const resourceIds = [0, 1];
      const estimateHours = [10, 10];

      let tx = await UsageTrackingContract.connect(deployer).startMultiSessions(
        resourceIds,
        estimateHours
      );
      await tx.wait();

      const sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      assert(sessionData.length === 2);
      await ethers.provider.send("evm_increaseTime", [3600]); // Increase time by 1 hour

      tx = await UsageTrackingContract.connect(deployer).endMultiSessions(
        sessionData
      );
      await tx.wait();

      const lessorBalance = await PricingContract.userBalances(lessor.address);

      assert(
        lessorBalance.toString() === ethers.utils.parseEther("2").toString()
      );
    });

    it("Start multi session, end multi session and withdraw", async () => {
      await registerMultiResource();
      const resourceIds = [0, 1];
      const estimateHours = [10, 10];

      let tx = await UsageTrackingContract.connect(deployer).startMultiSessions(
        resourceIds,
        estimateHours
      );
      await tx.wait();

      const sessionData = await UsageTrackingContract.getActiveSessionByAddress(
        deployer.address
      );

      assert(sessionData.length === 2);
      await ethers.provider.send("evm_increaseTime", [3600]); // Increase time by 1 hour

      tx = await UsageTrackingContract.connect(deployer).endMultiSessions(
        sessionData
      );
      await tx.wait();

      const lessorBalance = await PricingContract.userBalances(lessor.address);

      assert(
        lessorBalance.toString() === ethers.utils.parseEther("2").toString()
      );

      tx = await PricingContract.connect(lessor).withdrawTokens(lessorBalance);
      await tx.wait();

      const axbBalance = await AxBContract.balanceOf(lessor.address);
      assert(axbBalance.toString() === lessorBalance.toString());
    });
  });
});
