import subprocess
import time
import sys
import os

def launch_satellite_network():
    # Configuration for 5 satellites
    satellites = [
        {"node_num": 1, "port": 8081, "sat_index": 0},
        {"node_num": 2, "port": 8082, "sat_index": 1},
        {"node_num": 3, "port": 8083, "sat_index": 2},
        {"node_num": 4, "port": 8084, "sat_index": 3},
        {"node_num": 5, "port": 8085, "sat_index": 4}
    ]

    # Specific IP address
    # SERVER_IP = '10.35.70.31'
    SERVER_IP = 'localhost'

    processes = []
    
    for sat in satellites:
        # Create modified version of the server code for each satellite
        config = f"""
if __name__ == "__main__":
    # Configuration
    global_dequeue = deque(maxlen=10)
    NUM_SATS = 5
    SAT_INDEX = {sat['sat_index']}
    SAT_NODE_NUM = {sat['node_num']}
    ORBIT_Z_AXIS = (0, 0)
    VELOCITY = 27000/111.3/(60*60)  # degrees per second
    SERVER_ADDR = ('{SERVER_IP}', {sat['port']})
    BUFFER_SIZE = 1024
    
    # Initialize ISL network
    isl_network = InterSatelliteLinks(NUM_SATS, max_isl_distance=2000)
    
    # Create threads
    simulation_thread = threading.Thread(
        target=keep_moving,
        args=(global_dequeue, ORBIT_Z_AXIS, NUM_SATS, VELOCITY, SAT_INDEX, isl_network),
        daemon=True
    )
    
    server_thread = threading.Thread(
        target=server,
        args=(global_dequeue, SERVER_ADDR, BUFFER_SIZE, SAT_NODE_NUM, isl_network),
        daemon=True
    )
    
    # Start threads
    simulation_thread.start()
    server_thread.start()
    
    # Keep main program alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting..")
"""
        
        # Create a temporary file for this satellite
        filename = f"satellite_{sat['node_num']}.py"
        with open(filename, 'w') as f:
            # Copy the original code except the main block
            with open('satellite_server.py', 'r') as original:
                for line in original:
                    if "__main__" not in line:
                        f.write(line)
            # Add our custom configuration
            f.write(config)
        
        # Launch the satellite process
        process = subprocess.Popen([sys.executable, filename])
        processes.append(process)
        print(f"Launched satellite {sat['node_num']} on IP {SERVER_IP}:{sat['port']}")
        time.sleep(2)  # Wait a bit between launches to prevent race conditions
    
    print(f"\nAll satellites launched on IP {SERVER_IP}! Network is operational.")
    print("Press Ctrl+C to shutdown the network.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down satellite network...")
        for p in processes:
            p.terminate()
        # Clean up temporary files
        for sat in satellites:
            try:
                os.remove(f"satellite_{sat['node_num']}.py")
            except:
                pass
        print("Network shutdown complete.")

if __name__ == "__main__":
    launch_satellite_network()