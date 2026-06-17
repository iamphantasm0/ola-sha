import { expect } from "chai";
import { ethers } from "hardhat";
import { OlaRegistry } from "../typechain-types";

describe("OlaRegistry", () => {
  let registry: OlaRegistry;
  let ownerAddr: string;
  let other: any;

  const orderId = ethers.keccak256(ethers.toUtf8Bytes("order-uuid-1"));
  const storageHash = "0xabc123rootHashFrom0GStorage";

  beforeEach(async () => {
    const [owner, otherSigner] = await ethers.getSigners();
    ownerAddr = owner.address;
    other = otherSigner;
    const Registry = await ethers.getContractFactory("OlaRegistry");
    registry = (await Registry.deploy(ownerAddr)) as unknown as OlaRegistry;
    await registry.waitForDeployment();
  });

  it("logs a settlement and emits OrderSettled", async () => {
    await expect(registry.logSettlement(orderId, "offramp", "NGN", 20000, storageHash))
      .to.emit(registry, "OrderSettled")
      .withArgs(orderId, "offramp", "NGN", 20000, storageHash);

    const s = await registry.getSettlement(orderId);
    expect(s.direction).to.equal("offramp");
    expect(s.currency).to.equal("NGN");
    expect(s.amount).to.equal(20000n);
    expect(s.storageHash).to.equal(storageHash);
    expect(s.settledAt).to.be.greaterThan(0n);
    expect(await registry.totalSettlements()).to.equal(1n);
  });

  it("reverts on duplicate orderId (idempotency guard)", async () => {
    await registry.logSettlement(orderId, "offramp", "NGN", 20000, storageHash);
    await expect(
      registry.logSettlement(orderId, "offramp", "NGN", 20000, storageHash)
    ).to.be.revertedWith("Already logged");
  });

  it("only owner can log", async () => {
    await expect(
      registry.connect(other).logSettlement(orderId, "onramp", "KES", 5000, storageHash)
    ).to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount");
  });
});
