import random
import argparse

def generate_trace():
    parser = argparse.ArgumentParser(description="PCER Traffic Generator")
    parser.add_argument("--burst", action="store_true", help="Enable burst mode")
    parser.add_argument("--burst-size", type=int, default=10, help="Number of packets per burst")
    parser.add_argument("--burst-interval", type=float, default=0.01, help="Interval between burst packets")
    parser.add_argument("--burst-count", type=int, default=3, help="Number of bursts during simulation")
    args = parser.parse_args()

    print(f"Generating traffic_trace.txt... (Burst mode: {args.burst})")
    with open("traffic_trace.txt", "w") as f:
        # Simulate 100 seconds of factory data
        current_time = 0.0
        
        # Pre-schedule bursts if enabled
        burst_times = []
        if args.burst:
            for _ in range(args.burst_count):
                burst_times.append(random.uniform(5.0, 95.0))
            burst_times.sort()

        for i in range(100):
            # Check if we should trigger a burst
            if burst_times and current_time >= burst_times[0]:
                burst_times.pop(0)
                for b in range(args.burst_size):
                    src = random.randint(0, 4)
                    dst = random.randint(0, 4)
                    while dst == src: dst = random.randint(0, 4)
                    f.write(f"{(current_time + b * args.burst_interval):.2f} {src} {dst} 512 0\n")
                current_time += args.burst_size * args.burst_interval
            # 10% chance of CRITICAL, 50% BULK, 40% STANDARD
            rand_val = random.random()
            
            if rand_val < 0.1: # Critical (Ambulance)
                tag = 0 
                size = 512  # Small block
                interval = 0.1 
            elif rand_val < 0.6: # Bulk (Cargo Truck)
                tag = 2
                size = 4096 # Big block
                interval = 1.0
            else: # Standard
                tag = 1
                size = 1024
                interval = 0.5
            
            current_time += interval
            
            # Format: [Time] [SourceNode] [DestNode] [Size] [TAG]
            # Example: At 1.5s, Node 0 sends to Node 4, size 512, TAG 0
            # We'll use random source/dest for variety, assuming 5 nodes (0-4)
            src = random.randint(0, 4)
            dst = random.randint(0, 4)
            while dst == src:
                dst = random.randint(0, 4)
                
            line = f"{current_time:.2f} {src} {dst} {size} {tag}\n"
            f.write(line)

    print("Trace file generated: traffic_trace.txt")

if __name__ == "__main__":
    generate_trace()
