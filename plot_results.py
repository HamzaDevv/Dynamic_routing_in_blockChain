import matplotlib.pyplot as plt
import csv

def plot_results():
    print("Reading pcer_results.csv...")
    
    methods = []
    tags = []
    latencies = []
    lives = []
    
    try:
        with open('pcer_results.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                methods.append(row['Method'])
                tags.append(row['Tag'])
                latencies.append(float(row['Latency']))
                lives.append(float(row['NetworkLife']))
    except FileNotFoundError:
        print("Error: pcer_results.csv not found.")
        return

    # Filter for Critical Tag Latency
    baseline_latency = 0
    pcer_latency = 0
    
    for i in range(len(methods)):
        if tags[i] == 'Critical':
            if methods[i] == 'Baseline':
                baseline_latency = latencies[i]
            elif methods[i] == 'PCER':
                pcer_latency = latencies[i]

    # Graph 1: Latency Comparison (Critical Traffic)
    plt.figure(figsize=(8, 6))
    plt.bar(['Baseline (Old)', 'PCER (New)'], [baseline_latency, pcer_latency], color=['red', 'green'])
    plt.title('Average Latency for Critical Traffic (Tag 0)')
    plt.ylabel('Latency (ms)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save graph
    plt.savefig('latency_comparison.png')
    print("Saved latency_comparison.png")
    
    # Graph 2: Network Life Comparison (Overall)
    # Assuming NetworkLife is the same for all tags in a method for this simple plot
    baseline_life = 0
    pcer_life = 0
    
    for i in range(len(methods)):
        if methods[i] == 'Baseline':
            baseline_life = lives[i]
        elif methods[i] == 'PCER':
            pcer_life = lives[i]
            
    plt.figure(figsize=(8, 6))
    plt.bar(['Baseline (Old)', 'PCER (New)'], [baseline_life, pcer_life], color=['gray', 'blue'])
    plt.title('Network Lifetime (Battery Remaining)')
    plt.ylabel('Battery Level (%)')
    plt.ylim(0, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save graph
    plt.savefig('network_life_comparison.png')
    print("Saved network_life_comparison.png")

if __name__ == "__main__":
    plot_results()
