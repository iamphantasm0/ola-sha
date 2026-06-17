import { ethers } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying OlaRegistry with:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Deployer balance:", ethers.formatEther(balance), "0G");

  // Owner = deployer (the backend signer that will call logSettlement)
  const Registry = await ethers.getContractFactory("OlaRegistry");
  const registry = await Registry.deploy(deployer.address);
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log("OlaRegistry deployed to:", address);
  console.log("→ Set REGISTRY_CONTRACT_ADDRESS=%s in .env", address);
  console.log("→ Verify on https://chainscan-galileo.0g.ai/address/%s", address);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
