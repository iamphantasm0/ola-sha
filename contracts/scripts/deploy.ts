import { ethers, network } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();
  const balance = await ethers.provider.getBalance(deployer.address);

  console.log(`Network:  ${network.name}`);
  console.log(`Deployer: ${deployer.address}`);
  console.log(`Balance:  ${ethers.formatEther(balance)} OG`);

  if (balance === 0n) {
    throw new Error(
      "Deployer has 0 OG. Fund it at https://faucet.0g.ai (0.1 OG/day) before deploying."
    );
  }

  const Registry = await ethers.getContractFactory("OlaRegistry");
  const registry = await Registry.deploy(deployer.address);
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log("\n✅ OlaRegistry deployed");
  console.log(`   address: ${address}`);
  console.log(`\nAdd this to your root .env:\n   REGISTRY_CONTRACT_ADDRESS=${address}\n`);
  console.log(`Explorer: https://chainscan-galileo.0g.ai/address/${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
