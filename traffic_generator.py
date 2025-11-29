import random

def generate_trace():
    print("Generating traffic_trace.txt...")
    with open("traffic_trace.txt", "w") as f:
        # Simulate 100 seconds of factory data
        current_time = 0.0
        
        for i in range(100):
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
