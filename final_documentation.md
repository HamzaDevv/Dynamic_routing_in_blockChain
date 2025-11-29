# PCER Project: Final Implementation Guide

This document contains the complete guide to setting up and running your Priority-Coupled Elastic Routing (PCER) project in NS3.

## 1. Project Structure
Your workspace contains the following files:

### Traffic Generation
- `traffic_generator.py`: Generates the `traffic_trace.txt` file.
- `traffic_trace.txt`: The input file for the simulation.

### NS3 Implementation (The "Muscle")
These files implement the custom routing protocol.
- `ns3/pcer_tag.h`: Defines the packet tag for urgency.
- `ns3/pcer-routing-protocol.h`: Header for the routing protocol.
- `ns3/pcer-routing-protocol.cc`: **CORE LOGIC**. Contains the `CalculateCost` function with your weights.
- `ns3/pcer-helper.h`: Helper to install the protocol.
- `ns3/pcer_sim.cc`: The main simulation script.

### Analysis
- `plot_results.py`: Generates graphs from the CSV output.
- `pcer_results.csv`: Example output file.

## 2. Setup Instructions

### Step A: Generate Traffic
Run the generator to create the trace file:
```bash
python3 traffic_generator.py
```

### Step B: Integrate with NS3
1. **Install NS3**: Ensure you have a working NS3 environment (e.g., `ns-3.35`).
2. **Copy Files**:
   - Copy `traffic_trace.txt` to your NS3 root directory (where you run `./waf`).
   - Copy `ns3/pcer_sim.cc` to `scratch/pcer_sim.cc`.
   - Copy `ns3/pcer_tag.h`, `ns3/pcer-routing-protocol.h`, `ns3/pcer-routing-protocol.cc`, `ns3/pcer-helper.h` to `src/internet/model/` (or create a new module `src/pcer/model/`).
   - **Note**: If you put them in `scratch/`, you might need to modify `wscript` or just include the `.cc` files directly in `pcer_sim.cc` (not recommended but works for quick tests).
   - **Easiest Method**: Put ALL `.h` and `.cc` files in `scratch/` alongside `pcer_sim.cc` and update the includes if necessary.

### Step C: Compile and Run
Run the simulation using Waf:
```bash
./waf --run scratch/pcer_sim
```
This will generate `pcer_results_real.csv`.

### Step D: Analyze Results
Run the plotting script:
```bash
python3 plot_results.py
```
(Make sure to point it to `pcer_results_real.csv` if you want to plot the new data).

## 3. Implementation Details

### The "Cost" Function
The heart of your project is in `ns3/pcer-routing-protocol.cc`:
```cpp
double PcerRoutingProtocol::CalculateCost (uint8_t tag, const NeighborInfo& neighbor)
{
    // ... Weights definition ...
    if (tag == 0) { // CRITICAL
        w1_delay = 100.0; 
        w2_energy = 0.0;  
    }
    // ...
    return (w1_delay * neighbor.delay) + (w2_energy * energy_cost);
}
```
You can modify the weights here to tune the performance.

## 4. Verification
- **Latency Graph**: Should show Critical traffic (Tag 0) has lower latency in PCER mode.
- **Network Life**: Should show balanced energy usage.

Good luck with your project!
