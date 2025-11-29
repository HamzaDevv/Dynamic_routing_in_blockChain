#include "ns3/core-module.h"
#include "ns3/internet-module.h"
#include "ns3/ipv4-routing-protocol.h"
#include "ns3/network-module.h"
#include "pcer_tag.h" // Include our custom tag
#include <cstdint>

// Note: This is a simplified representation of where the logic would go.
// In a real NS3 implementation, this would be part of a class like
// AodvRoutingProtocol or a new class PcerRoutingProtocol.

namespace ns3 {

// Assuming a structure or class for Neighbor information
struct NeighborInfo {
  double delay;  // Link delay
  double energy; // Remaining energy of the neighbor (0.0 to 1.0 or Joules)
};

/**
 * @brief Calculates the link metric/cost based on PCER logic.
 *
 * @param p The packet being forwarded.
 * @param neighbor Information about the neighbor node.
 * @return double The calculated cost (lower is better).
 */
double GetMetric(Ptr<const Packet> p, NeighborInfo neighbor) {
  // 1. Get the Tag from the packet
  PcErTag urgencyTag;
  uint8_t tag = 1; // Default to Standard if tag is missing

  if (p->PeekPacketTag(urgencyTag)) {
    tag = urgencyTag.Get();
  }

  // 2. Set Weights based on PCER proposal
  double w1_delay = 1.0;
  double w2_energy = 1.0;

  if (tag == 0) { // CRITICAL
    // Needs speed. High penalty for delay.
    // Ignore energy cost (set weight to 0 or very low).
    w1_delay = 100.0;
    w2_energy = 0.0;
  } else if (tag == 2) { // BULK
    // Needs to save energy. High penalty for wasting energy.
    // Ignore delay (set weight to 0 or very low).
    w1_delay = 0.0;
    w2_energy = 100.0;
  } else { // STANDARD (Tag 1)
    // Balanced approach.
    w1_delay = 1.0;
    w2_energy = 1.0;
  }

  // Avoid division by zero if energy is 0
  double energy_cost =
      (neighbor.energy > 0.0001) ? (1.0 / neighbor.energy) : 10000.0;

  // 3. Calculate Final Score
  // Cost = (w1 * Delay) + (w2 * (1 / Energy))
  double score = (w1_delay * neighbor.delay) + (w2_energy * energy_cost);

  return score;
}

} // namespace ns3
