// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title PCERRouting — Priority-Coupled Elastic Routing on-chain engine
/// @notice Implements PCER-T v4 multi-objective cost function.
///         Routing decisions are *view* calls (zero gas via eth_call / staticCall).
///         Only path-logging emits a state-changing transaction (cheap audit trail).
contract PCERRouting {

    // ── Data Structures ──────────────────────────────────────────────
    struct Node {
        uint256 id;
        uint256 battery; // scaled: 10000 = 100%
        uint256 trust;   // scaled: 10000 = 1.0
        bool    isDead;
    }

    struct Edge {
        uint256 delay; // ms
        uint256 etx;   // scaled: 100 = 1.0
    }

    // ── State ────────────────────────────────────────────────────────
    mapping(uint256 => Node) public nodes;
    mapping(uint256 => mapping(uint256 => Edge)) public edges;

    /// @notice On-chain adjacency list — populated by setEdge
    mapping(uint256 => uint256[]) public adjacency;

    /// @notice Hysteresis memory: stores last chosen hop per source
    mapping(uint256 => uint256) public lastBestHop;
    /// @notice Hysteresis memory: stores last best cost per source
    mapping(uint256 => uint256) public lastBestCost;

    // ── Constants ────────────────────────────────────────────────────
    uint256 public constant BAT_HARD      = 500;   // 5%
    uint256 public constant BAT_SOFT      = 2500;  // 25%
    uint256 public constant DEST          = 17;    // cloud gateway
    uint256 public constant HYST_BAND_PCT = 5;     // 5% improvement required to switch

    // V4 Weights (scaled by 100)
    uint256 constant W0_D = 70; uint256 constant W0_E = 8;  uint256 constant W0_T = 14; uint256 constant W0_ETX = 6;  uint256 constant W0_L = 2;
    uint256 constant W1_D = 38; uint256 constant W1_E = 30; uint256 constant W1_T = 18; uint256 constant W1_ETX = 8;  uint256 constant W1_L = 6;
    uint256 constant W2_D = 4;  uint256 constant W2_E = 60; uint256 constant W2_T = 20; uint256 constant W2_ETX = 10; uint256 constant W2_L = 6;

    // ── Events ───────────────────────────────────────────────────────
    event NodeStateUpdated(uint256 indexed nodeId, uint256 battery, uint256 trust);
    /// @notice Emitted once per hop decision — this is the immutable audit trail
    event PathSelected(
        bytes32 indexed packetId,
        uint256 indexed source,
        uint256 indexed chosenHop,
        uint256 cost,
        uint8   tag,
        uint256 timestamp
    );

    // ── Admin: Topology Initialisation ───────────────────────────────
    function setNode(uint256 id, uint256 battery, uint256 trust, bool isDead) external {
        nodes[id] = Node(id, battery, trust, isDead);
        emit NodeStateUpdated(id, battery, trust);
    }

    function setEdge(uint256 u, uint256 v, uint256 delay, uint256 etx) external {
        edges[u][v] = Edge(delay, etx);

        // Maintain on-chain adjacency list (deduplicated)
        bool found = false;
        uint256[] storage nbrs = adjacency[u];
        for (uint i = 0; i < nbrs.length; i++) {
            if (nbrs[i] == v) { found = true; break; }
        }
        if (!found) nbrs.push(v);
    }

    // ── Internal: Dead-End Check (fully on-chain) ────────────────────
    /// @dev Returns true if vn has no viable exits (except back to cur).
    function _isDeadEnd(uint256 cur, uint256 vn) internal view returns (bool) {
        if (vn == DEST) return false;
        uint256[] storage exits = adjacency[vn];
        for (uint i = 0; i < exits.length; i++) {
            uint256 exit = exits[i];
            if (exit == cur) continue;
            if (nodes[exit].battery >= BAT_HARD) return false;
        }
        return true;
    }

    // ── Core: Cost Function (VIEW — zero gas via staticCall) ─────────
    /// @notice Pure multi-objective PCER-T v4 cost for edge (u → vn).
    ///         Call this via eth_call / staticCall — no gas consumed.
    function calculateCostV4(uint8 tag, uint256 u, uint256 vn) public view returns (uint256) {
        if (vn != DEST && nodes[vn].battery < BAT_HARD) return type(uint256).max;
        if (_isDeadEnd(u, vn)) return type(uint256).max;

        Node memory neighbor = nodes[vn];
        Edge memory edge     = edges[u][vn];

        uint256 bat = neighbor.battery;
        uint256 tr  = neighbor.trust;

        uint256 w_d; uint256 w_e; uint256 w_t; uint256 w_etx;
        if      (tag == 0) { w_d = W0_D; w_e = W0_E; w_t = W0_T; w_etx = W0_ETX; }
        else if (tag == 1) { w_d = W1_D; w_e = W1_E; w_t = W1_T; w_etx = W1_ETX; }
        else               { w_d = W2_D; w_e = W2_E; w_t = W2_T; w_etx = W2_ETX; }

        // ① ETX penalty
        uint256 etxPenalty = edge.etx > 100 ? (edge.etx - 100) * 12 : 0;

        // ② Trust + ETX compound
        uint256 trustBase       = ((10000 - tr) * 20) / 100;
        uint256 etxTrustCompound = (etxPenalty * (10000 - tr)) / 10000;

        // ③ Cubic energy floor
        uint256 ePenalty;
        if (bat < BAT_SOFT && vn != DEST) {
            uint256 ratio = (BAT_SOFT * 100) / bat;
            ePenalty = (ratio * ratio * ratio * 100) / 1000000;
        } else {
            ePenalty = bat > 0 ? (1000000 / bat) * 2 : 100000;
        }

        return (edge.delay * w_d) + (ePenalty * w_e) + (trustBase * w_t) + ((etxPenalty + etxTrustCompound) * w_etx);
    }

    // ── Core: Route Selection (VIEW — zero gas) ──────────────────────
    /// @notice Returns the best next hop and its cost for a given source node.
    ///         Call via staticCall — zero gas, instant response.
    ///         On-chain hysteresis is applied using stored lastBestHop/Cost.
    function getNextHop(
        uint256 source,
        uint8   tag,
        uint256[] calldata neighbors
    ) external view returns (uint256 bestHop, uint256 minCost) {
        minCost = type(uint256).max;
        bestHop = source;

        for (uint i = 0; i < neighbors.length; i++) {
            uint256 n    = neighbors[i];
            uint256 cost = calculateCostV4(tag, source, n);
            if (cost < minCost) { minCost = cost; bestHop = n; }
        }

        // On-chain MRHOF Hysteresis: only switch if improvement > HYST_BAND_PCT
        uint256 prevHop  = lastBestHop[source];
        uint256 prevCost = lastBestCost[source];
        if (prevHop != 0 && prevHop != bestHop && prevCost < type(uint256).max && prevCost > 0) {
            // improvement = (prevCost - minCost) / prevCost * 100
            if (prevCost > minCost) {
                uint256 improvement = ((prevCost - minCost) * 100) / prevCost;
                if (improvement < HYST_BAND_PCT) {
                    // Hysteresis: re-evaluate cost of previous hop
                    uint256 prevHopCost = calculateCostV4(tag, source, prevHop);
                    if (prevHopCost < type(uint256).max) {
                        bestHop = prevHop;
                        minCost = prevHopCost;
                    }
                }
            }
        }
    }

    // ── Audit Trail: Path Logger (STATE-CHANGING — cheap tx) ─────────
    /// @notice Call AFTER the routing decision to log the chosen path on-chain.
    ///         This is the only gas-consuming operation per hop.
    ///         Also updates on-chain hysteresis memory.
    function logPath(
        bytes32 packetId,
        uint256 source,
        uint256 chosenHop,
        uint256 cost,
        uint8   tag
    ) external {
        // Update on-chain hysteresis state
        lastBestHop[source]  = chosenHop;
        lastBestCost[source] = cost;

        emit PathSelected(packetId, source, chosenHop, cost, tag, block.timestamp);
    }
}
