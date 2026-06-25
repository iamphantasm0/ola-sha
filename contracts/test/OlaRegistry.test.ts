import { expect } from "chai";
import { ethers } from "hardhat";

describe("OlaRegistry", () => {
  async function deploy() {
    const [owner, other] = await ethers.getSigners();
    const Registry = await ethers.getContractFactory("OlaRegistry");
    const registry = await Registry.deploy(owner.address);
    await registry.waitForDeployment();
    return { registry, owner, other };
  }

  it("logs a settlement and emits OrderSettled", async () => {
    const { registry } = await deploy();
    const orderId = ethers.id("order-uuid-1"); // keccak256 of the string

    await expect(
      registry.logSettlement(orderId, "offramp", "NGN", 20000, "0xroothash")
    )
      .to.emit(registry, "OrderSettled")
      .withArgs(orderId, "offramp", "NGN", 20000, "0xroothash");

    const s = await registry.getSettlement(orderId);
    expect(s.direction).to.equal("offramp");
    expect(s.currency).to.equal("NGN");
    expect(s.amount).to.equal(20000n);
    expect(s.storageHash).to.equal("0xroothash");
    expect(s.settledAt).to.be.greaterThan(0n);
    expect(await registry.totalSettlements()).to.equal(1n);
  });

  it("rejects a duplicate orderId", async () => {
    const { registry } = await deploy();
    const orderId = ethers.id("order-uuid-2");
    await registry.logSettlement(orderId, "onramp", "KES", 10000, "0xa");
    await expect(
      registry.logSettlement(orderId, "onramp", "KES", 10000, "0xa")
    ).to.be.revertedWith("Already logged");
  });

  it("only the owner can log", async () => {
    const { registry, other } = await deploy();
    const orderId = ethers.id("order-uuid-3");
    await expect(
      registry.connect(other).logSettlement(orderId, "onramp", "BRL", 5000, "0xb")
    ).to.be.revertedWithCustomError(registry, "OwnableUnauthorizedAccount");
  });
});
