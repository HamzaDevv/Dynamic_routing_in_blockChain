const hre = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  const PCERRouting = await hre.ethers.getContractFactory("PCERRouting");
  const pcer = await PCERRouting.deploy();
  await pcer.waitForDeployment();
  const address = await pcer.getAddress();
  
  console.log("PCERRouting deployed to:", address);

  // Initialize network topology matching the HTML demo
  console.log("Initializing nodes and edges...");

  const nodeDefs = [
    { id: 0, battery: 10000, type: 'mains' },
    { id: 1, battery: 10000, type: 'mains' },
    { id: 2, battery: 2000, type: 'fast' },
    { id: 3, battery: 8000, type: 'med' },
    { id: 4, battery: 10000, type: 'mains' },
    { id: 5, battery: 3000, type: 'med' },
    { id: 6, battery: 10000, type: 'mains' },
    { id: 7, battery: 4000, type: 'med' },
    { id: 8, battery: 1500, type: 'fast' },
    { id: 9, battery: 10000, type: 'mains' },
    { id: 10, battery: 6000, type: 'fast' },
    { id: 11, battery: 10000, type: 'mains' },
    { id: 12, battery: 10000, type: 'mains' },
    { id: 13, battery: 5000, type: 'med' },
    { id: 14, battery: 10000, type: 'mains' },
    { id: 15, battery: 2500, type: 'fast' },
    { id: 16, battery: 7000, type: 'med' },
    { id: 17, battery: 10000, type: 'mains' },
  ];

  for (const n of nodeDefs) {
    const trust = 7000; // 0.7
    await pcer.setNode(n.id, n.battery, trust, false);
  }

  const edges = [
    [0, 1, 10], [0, 2, 5], [0, 3, 15], [0, 4, 20],
    [1, 5, 15], [2, 6, 10], [3, 7, 20], [4, 8, 15],
    [5, 9, 20], [6, 10, 15], [7, 11, 10], [8, 12, 5],
    [9, 13, 10], [10, 14, 20], [11, 15, 5], [12, 16, 10],
    [13, 17, 20], [14, 17, 15], [15, 17, 10], [16, 17, 25],
    [1, 2, 5], [2, 3, 10], [5, 6, 10], [7, 8, 10],
    [9, 10, 5], [11, 12, 5], [13, 14, 10], [15, 16, 5],
  ];

  for (const e of edges) {
    const [u, v, delay] = e;
    await pcer.setEdge(u, v, delay, 100); // etx 1.0 (100)
    await pcer.setEdge(v, u, delay, 100);
  }

  console.log("Topology initialized on-chain!");
  
  // Write address and ABI to a JS file that index_dapp.html can load
  const artifact = JSON.parse(fs.readFileSync("./artifacts/contracts/PCERRouting.sol/PCERRouting.json", "utf8"));
  
  const jsContent = `
    const CONTRACT_ADDRESS = "${address}";
    const CONTRACT_ABI = ${JSON.stringify(artifact.abi)};
  `;
  
  fs.writeFileSync("./contractData.js", jsContent);
  console.log("Wrote contractData.js");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
