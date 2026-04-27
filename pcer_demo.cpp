#include <iostream>
#include <vector>
#include <string>
#include <limits>
#include <iomanip>
#include <cmath>

// --- MOCK NS-3 CLASSES ---
struct NeighborInfo {
    std::string addr;
    double delay;
    double energy;
    double queue_size;
    double trust_score;
    double etx;
    double jitter;
    uint32_t packets_received;
    uint32_t packets_forwarded;
    double report_consistency;
    uint32_t load_count;
};

// --- PCER LOGIC (COPIED FROM IMPLEMENTATION) ---
double CalculateCost(uint8_t tag, const NeighborInfo &neighbor, double distanceToDest) {
  // PCER-v5 5-component cost function
  double wd, we, wt, wetx, wl;
  if (tag == 0) { // CRITICAL
    wd = 0.70; we = 0.08; wt = 0.14; wetx = 0.06; wl = 0.02;
  } else if (tag == 2) { // BULK
    wd = 0.04; we = 0.60; wt = 0.20; wetx = 0.10; wl = 0.06;
  } else { // STANDARD
    wd = 0.38; we = 0.30; wt = 0.18; wetx = 0.08; wl = 0.06;
  }

  // Hard guards
  if (neighbor.energy < 0.03) {
    return std::numeric_limits<double>::max();
  }

  double delay_cost = (neighbor.delay + distanceToDest) * wd;
  
  double e_penalty;
  if (neighbor.energy < 0.08) {
     e_penalty = std::pow(0.08 / neighbor.energy, 3) * 100.0;
  } else {
     e_penalty = (1.0 / neighbor.energy) * 2.0;
  }
  double energy_cost = e_penalty * we;

  double trust = neighbor.trust_score > 0 ? neighbor.trust_score : 0.7;
  double trust_base = (1.0 - trust) * 20.0;
  double trust_cost = trust_base * wt;

  double etx = neighbor.etx > 0 ? neighbor.etx : 1.0;
  double etx_penalty = std::max(0.0, (etx - 1.0) * 12.0);
  double etx_x_trust = etx_penalty * (1.0 - trust);
  double etx_cost = (etx_penalty + etx_x_trust) * wetx;

  double load_cost = neighbor.load_count * 0.7 * wl;

  double congestion_penalty = 0.0;
  if (neighbor.queue_size > 0.8) {
      congestion_penalty = std::pow((neighbor.queue_size - 0.8) / 0.2, 2) * 200.0;
  } else if (neighbor.queue_size > 0.5) {
      congestion_penalty = (neighbor.queue_size - 0.5) * 20.0;
  }

  return delay_cost + energy_cost + trust_cost + etx_cost + load_cost + congestion_penalty;
}

int main() {
    // --- SETUP SIMULATION ---
    double energyNode2 = 0.10; // Fast Node (Starts Low)
    double energyNode3 = 1.00; // Slow Node (Starts High)
    
    NeighborInfo n2 = {"10.1.1.2", 5.0, energyNode2, 0.0, 0.5, 1.0, 0.0, 0, 0, 1.0, 0};
    NeighborInfo n3 = {"10.1.1.3", 50.0, energyNode3, 0.0, 0.9, 1.0, 0.0, 0, 0, 1.0, 0};

    std::cout << "\n=== PCER DYNAMIC SIMULATION (STANDALONE) ===\n";
    std::cout << "Scenario: Sending Critical Data (Tag 0).\n";
    std::cout << "Node 2: Delay 5ms (Preferred)\n";
    std::cout << "Node 3: Delay 50ms (Backup)\n";
    std::cout << "-----------------------------------------------------------------\n";
    std::cout << "| Time | Node 2 Bat | Cost (N2) | Cost (N3) | Routing Decision    |\n";
    std::cout << "-----------------------------------------------------------------\n";

    // --- SIMULATION LOOP ---
    for (int t = 0; t <= 10; t++) {
        // Update neighbors
        n2.energy = energyNode2;
        n3.energy = energyNode3;

        // Calculate Costs
        double cost2 = CalculateCost(0, n2, 0.0);
        double cost3 = CalculateCost(0, n3, 0.0);

        // Make Decision
        std::string decision;
        std::string n2_cost_str = (cost2 > 100000) ? "INF" : std::to_string((int)cost2);
        std::string n3_cost_str = (cost3 > 100000) ? "INF" : std::to_string((int)cost3);

        if (cost2 < cost3) {
            decision = "Node 2 (Fast)";
            // Simulate battery drain on the active node
            if (energyNode2 > 0) energyNode2 -= 0.01; 
        } else {
            decision = "-> SWITCH -> Node 3";
            // Node 3 would drain in reality, but for this demo we focus on the switch
        }

        // Print Row
        std::cout << "| " << std::setw(3) << t << "s |    " 
                  << std::setw(3) << (int)(n2.energy * 100) << "%    | " 
                  << std::setw(9) << n2_cost_str << " | "
                  << std::setw(9) << n3_cost_str << " | "
                  << std::left << std::setw(20) << decision << "|\n";
    }

    std::cout << "-----------------------------------------------------------------\n";
    return 0;
}
