// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "hardhat/console.sol";

contract PCERRouting {
    struct Node {
        uint256 id;
        uint256 battery; // 10000 = 100%
        uint256 trust;   // 10000 = 1.0
        bool isDead;
    }

    struct Edge {
        uint256 delay;   // In ms
        uint256 etx;     // 100 = 1.0
    }

    mapping(uint256 => Node) public nodes;
    // u => v => Edge
    mapping(uint256 => mapping(uint256 => Edge)) public edges;

    uint256 public constant BAT_HARD = 500; // 5%
    uint256 public constant BAT_SOFT = 2500; // 25%

    event RouteComputed(uint256 indexed source, uint256 indexed chosenHop, uint256 cost, uint8 tag);
    event NodeStateUpdated(uint256 indexed nodeId, uint256 battery, uint256 trust);

    // V4 Weights (scaled by 100)
    // Tag 0 (Critical)
    uint256 constant W0_D = 70;
    uint256 constant W0_E = 8;
    uint256 constant W0_T = 14;
    uint256 constant W0_ETX = 6;
    uint256 constant W0_L = 2;

    // Tag 1 (Standard)
    uint256 constant W1_D = 38;
    uint256 constant W1_E = 30;
    uint256 constant W1_T = 18;
    uint256 constant W1_ETX = 8;
    uint256 constant W1_L = 6;

    // Tag 2 (Bulk)
    uint256 constant W2_D = 4;
    uint256 constant W2_E = 60;
    uint256 constant W2_T = 20;
    uint256 constant W2_ETX = 10;
    uint256 constant W2_L = 6;

    constructor() {
    }

    function setNode(uint256 id, uint256 battery, uint256 trust, bool isDead) external {
        nodes[id] = Node(id, battery, trust, isDead);
        emit NodeStateUpdated(id, battery, trust);
    }

    function setEdge(uint256 u, uint256 v, uint256 delay, uint256 etx) external {
        edges[u][v] = Edge(delay, etx);
    }

    // Cost computation scaled by 100
    function calculateCostV4(uint8 tag, uint256 u, uint256 vn, bool isDeadEnd) public view returns (uint256) {
        if (isDeadEnd) return type(uint256).max;

        Node memory neighbor = nodes[vn];
        Edge memory edge = edges[u][vn];

        // Hard guards
        if (neighbor.battery < BAT_HARD && vn != 17) { // 17 is DEST in JS
            return type(uint256).max;
        }

        uint256 bat = neighbor.battery; // up to 10000
        uint256 tr = neighbor.trust;    // up to 10000

        uint256 w_d; uint256 w_e; uint256 w_t; uint256 w_etx; uint256 w_l;
        if (tag == 0) { w_d = W0_D; w_e = W0_E; w_t = W0_T; w_etx = W0_ETX; w_l = W0_L; }
        else if (tag == 1) { w_d = W1_D; w_e = W1_E; w_t = W1_T; w_etx = W1_ETX; w_l = W1_L; }
        else { w_d = W2_D; w_e = W2_E; w_t = W2_T; w_etx = W2_ETX; w_l = W2_L; }

        // ① MRHOF-ETX: normalised link quality penalty
        // etx is scaled by 100. etx=100 means 1.0.
        uint256 etxPenalty = 0;
        if (edge.etx > 100) {
            etxPenalty = (edge.etx - 100) * 12; // scaled appropriately
        }

        // ② Dual Trust Compound
        // tr is scaled by 10000. 10000 means 1.0.
        uint256 trustBase = ((10000 - tr) * 20) / 100; // scaled
        uint256 etxTrustCompound = (etxPenalty * (10000 - tr)) / 10000;

        // ③ Energy floor
        uint256 ePenalty = 0;
        if (bat < BAT_SOFT && vn != 17) {
            // Cubic penalty approximated
            uint256 ratio = (BAT_SOFT * 100) / bat; 
            ePenalty = (ratio * ratio * ratio * 100) / 1000000; 
        } else {
            ePenalty = bat > 0 ? (1000000 / bat) * 2 : 100000;
        }

        uint256 delayCost = (edge.delay * w_d);
        uint256 energyCost = (ePenalty * w_e);
        uint256 trustCost = (trustBase * w_t);
        uint256 etxCost = ((etxPenalty + etxTrustCompound) * w_etx);

        // Load and congestion omitted or simplified in Smart Contract for now 
        // to focus on core metrics, can be injected via off-chain load counts.

        return delayCost + energyCost + trustCost + etxCost;
    }

    function getNextHop(uint256 source, uint8 tag, uint256[] calldata neighbors, bool[] calldata deadEnds) external returns (uint256 bestHop, uint256 minCost) {
        minCost = type(uint256).max;
        bestHop = source;

        for (uint i = 0; i < neighbors.length; i++) {
            uint256 n = neighbors[i];
            uint256 cost = calculateCostV4(tag, source, n, deadEnds[i]);
            
            if (cost < minCost) {
                minCost = cost;
                bestHop = n;
            }
        }

        emit RouteComputed(source, bestHop, minCost, tag);
        return (bestHop, minCost);
    }
}
