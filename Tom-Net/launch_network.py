import subprocess
import time
import sys
import os
from typing import List

def create_satellite_script(sat_id: int, sat_index: int, port: int, server_ip: str, num_sats: int, max_isl_distance: float) -> str:
    """
    Generates a satellite script file with the given configuration.
    """
    filename = f"satellite_{sat_id}.py"
    config = f"""
if __name__ == "__main__":
    # Configuration
    global_dequeue = deque(maxlen=10)
    NUM_SATS = {num_sats}
    SAT_INDEX = {sat_index}
    SAT_NODE_NUM = {sat_id}
    ORBIT_Z_AXIS = (0, 0)
    VELOCITY = 27000/111.3/(60*60)  # degrees per second
    SERVER_ADDR = ('{server_ip}', {port})
    BUFFER_SIZE = 1024
    
    # Initialize ISL network
    isl_network = InterSatelliteLinks(NUM_SATS, max_isl_distance={max_isl_distance})
    
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
        print("Satellite {sat_id} exiting...")
    """
    
    with open(filename, 'w') as f:
        with open('satellite_server.py', 'r') as original:
            for line in original:
                if "__main__" not in line:
                    f.write(line)
        f.write(config)
    
    return filename

def launch_satellite_network():
    # Configuration for satellites
    satellites = [
        {"node_num": 1, "port": 8081, "sat_index": 0},
        {"node_num": 2, "port": 8082, "sat_index": 1},
        {"node_num": 3, "port": 8083, "sat_index": 2},
        {"node_num": 4, "port": 8084, "sat_index": 3},
        {"node_num": 5, "port": 8085, "sat_index": 4}
    ]

    SERVER_IP = 'localhost'
    NUM_SATS = len(satellites)
    MAX_ISL_DISTANCE = 200000  # Adjust as needed
    
    processes = []
    try:
        for sat in satellites:
            script = create_satellite_script(
                sat_id=sat["node_num"],
                sat_index=sat["sat_index"],
                port=sat["port"],
                server_ip=SERVER_IP,
                num_sats=NUM_SATS,
                max_isl_distance=MAX_ISL_DISTANCE
            )
            # Launch the satellite process
            process = subprocess.Popen([sys.executable, script])
            processes.append(process)
            print(f"Launching Satellite {sat['node_num']} at {SERVER_IP}:{sat['port']}...")
            time.sleep(1)  # Avoid race conditions
            
        print("\nAll satellites launched! Press Ctrl+C to shut down.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down the satellite network...")
        for p in processes:
            p.terminate()
        for sat in satellites:
            os.remove(f"satellite_{sat['node_num']}.py")
        print("All satellites terminated.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    launch_satellite_network()
