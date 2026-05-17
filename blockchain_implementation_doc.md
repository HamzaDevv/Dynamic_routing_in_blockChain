# PCER-T v4 Blockchain Migration: Implementation Documentation

This document outlines the architectural changes, integrations, and optimizations implemented to migrate the PCER IoT simulation from a standalone client-side application to a decentralized Web3 architecture using **Hardhat**, **Solidity**, and **ethers.js**.

## 1. Architectural Overview
The goal of this migration was to offload the heavy routing cost calculations (the "brain") to an on-chain Smart Contract while maintaining the 60fps high-fidelity visual rendering (the "UI") on the frontend.

### Separation of Concerns:
* **The Smart Contract (`PCERRouting.sol`)**: Acts as the definitive source of truth for the routing algorithm. It calculates the Multi-Objective Cost Function and makes hop-by-hop routing decisions.
* **The Frontend (`index_dapp.html`)**: Simulates the physical IoT network, visualizes the nodes, and acts as the "client" that sends transaction requests to the Smart Contract whenever a packet needs to move.
* **The Bridge (`ethers.js`)**: The middleware that packages the frontend's routing requests into Ethereum transactions and handles the asynchronous responses.

---

## 2. Smart Contract Implementation (`PCERRouting.sol`)
The core routing logic was rewritten in Solidity `0.8.24`.

### A. Scaling Floating-Point Math
Because Solidity does not natively support floating-point numbers, the Javascript decimal calculations were scaled to integers:
* **Batteries:** Scaled up to `10000` (where `10000 = 100%`).
* **Trust & ETX:** Scaled mathematically to prevent precision loss during penalties.
* **Cubic Floor Penalty:** Approximated using scaled integer division to heavily penalize nodes dropping below the 5% `BAT_HARD` or 25% `BAT_SOFT` thresholds.

### B. Gas Optimization & `viaIR`
To avoid "Stack too deep" compilation errors caused by the complex multi-variable PCER formula, the Hardhat compiler (`hardhat.config.js`) was updated to use the **viaIR pipeline** and the **Solidity Optimizer**, significantly reducing the `Gas Used` per transaction.

---

## 3. Web3 Frontend Integration (`index_dapp.html`)
The traditional Javascript simulation was converted into a dynamic dApp.

### A. The `buildPath` Interception Hook
To prevent the blockchain's block-mining latency from stuttering the visual animation, the Web3 transactions are fired asynchronously. 
* When a packet prepares to move, the JS `buildPath()` function makes its physical animation decision, but **simultaneously fires an asynchronous `pcerContract.getNextHop` transaction** to the Hardhat node in the background.

### B. Live Terminal Dashboard
A new Web3 Blockchain panel was injected into the sidebar UI. It dynamically updates with:
* The current Sync Block.
* Total Gas Used.
* A live, terminal-styled printout of the latest transaction containing the Contract Call, Tx Hash, Gas limits, and Block Hash.

---

## 4. Resolving the "Greedy Trap" Issue (1-Hop Look-Ahead)
### The Problem:
Because the Smart Contract is designed for **Decentralized Hop-by-Hop** routing (unlike the global Dijkstra algorithm in early versions), packets were getting trapped at dead-end nodes (e.g., Node #4) whose only exits were dead or below the 5% survival threshold. 

### The Solution:
Instead of rewriting the Smart Contract to execute a massive, gas-heavy global Dijkstra search, a lightweight **1-Hop Look-Ahead** mechanism was implemented.
1. The JS frontend actively checks if the neighbor being evaluated has any valid exits remaining (`checkDeadEnd()`).
2. If the neighbor is a dead-end trap, the JS sets a boolean flag.
3. This boolean flag (`deadEnds`) is passed as an array directly into the `getNextHop` Smart Contract function.
4. The Solidity Smart Contract reads the flag, and if `true`, instantly assigns that path a cost of `Infinity`, cleanly avoiding the trap without spending heavy gas on graph traversal.

---

## 5. Visual UX Enhancements
### "Failed Intention" Visualization
When a packet drops (due to TTL expiration or network partitions), the simulation now dynamically calculates the "Ideal Route" (the shortest path based purely on physical delay). As the dropped packet fades out, a dashed red line is drawn from the failure node to the destination, clearly showing the route the packet *intended* to take had the network been healthy.

---

## 6. Deployment Infrastructure
The `scripts/deployPure.js` script handles automatic chain initialization. Upon execution, it:
1. Deploys the Smart Contract.
2. Synchronizes the 18 local JS nodes (Batteries & Trust) to the blockchain via `setNode()`.
3. Maps all physical connections to the blockchain via `setEdge()`.
4. Writes the ABI and deployed address to `contractData.js`, allowing the frontend to dynamically connect without hardcoded variables.

### How to Run:
```bash
# 1. Start the local chain
npx hardhat node

# 2. Deploy the contract & topology
node scripts/deployPure.js

# 3. View the dApp
Open index_dapp.html in browser.
```
