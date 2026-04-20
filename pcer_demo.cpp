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
};

// --- PCER LOGIC (COPIED FROM IMPLEMENTATION) ---
double CalculateCost(uint8_t tag, const NeighborInfo &neighbor) {
    // --- PCER CORE LOGIC ---
    double w1_delay = 1.0;
    double w2_energy = 1.0;

    if (tag == 0) { // CRITICAL
        w1_delay = 100.0;
        w2_energy = 0.0;
    } else if (tag == 2) { // BULK
        w1_delay = 0.0;
        w2_energy = 100.0;
    } else { // STANDARD
        w1_delay = 1.0;
        w2_energy = 1.0;
    }

    // --- SURVIVAL THRESHOLD ---
    // If battery is critical (< 5%), avoid this node at all costs.
    if (neighbor.energy < 0.05) {
        return std::numeric_limits<double>::max();
    }

    double energy_cost =
        (neighbor.energy > 0.0001) ? (1.0 / neighbor.energy) : 10000.0;
    return (w1_delay * neighbor.delay) + (w2_energy * energy_cost);
}

int main() {
    // --- SETUP SIMULATION ---
    double energyNode2 = 0.10; // Fast Node (Starts Low)
    double energyNode3 = 1.00; // Slow Node (Starts High)
    
    NeighborInfo n2 = {"10.1.1.2", 5.0, energyNode2};
    NeighborInfo n3 = {"10.1.1.3", 50.0, energyNode3};

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
        double cost2 = CalculateCost(0, n2);
        double cost3 = CalculateCost(0, n3);

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
