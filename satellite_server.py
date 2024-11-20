import logging
from collections import deque
import socket
import threading
import time
import numpy as np
from typing import Dict, Tuple

# Configure logging for clarity
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class ISLNode:
    def __init__(self, sat_id: int, lat: float, lon: float):
        self.sat_id = sat_id
        self.lat = lat
        self.lon = lon
        self.neighbors: Dict[int, Tuple[float, float]] = {}  # sat_id: (lat, lon)
        self.routing_table: Dict[int, int] = {}  # dest_id: next_hop_id
        self.last_update = time.time()

class InterSatelliteLinks:
    def __init__(self, num_satellites: int, max_isl_distance: float = 1000):
        self.num_satellites = num_satellites
        self.max_isl_distance = max_isl_distance
        self.satellites: Dict[int, ISLNode] = {}
        self.connection_lock = threading.Lock()
        
        logging.info(f"Initializing ISL network with {num_satellites} satellites...")
        
        # Initialize satellites with random positions
        for sat_id in range(self.num_satellites):
            lat = np.random.uniform(-90, 90)  # Random latitude
            lon = np.random.uniform(-180, 180)  # Random longitude
            self.satellites[sat_id] = ISLNode(sat_id, lat, lon)
            logging.info(f"Satellite {sat_id} initialized at position lat={lat:.2f}, lon={lon:.2f}.")
            self.update_neighbors(sat_id)

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        SAT_H = 550.0  # Satellite height in km
        EARTH_R = 6378.0  # Earth radius in km
        
        sat_r = EARTH_R + SAT_H
        x1 = sat_r * np.cos(np.radians(lat1)) * np.cos(np.radians(lon1))
        y1 = sat_r * np.cos(np.radians(lat1)) * np.sin(np.radians(lon1))
        z1 = sat_r * np.sin(np.radians(lat1))
        
        x2 = sat_r * np.cos(np.radians(lat2)) * np.cos(np.radians(lon2))
        y2 = sat_r * np.cos(np.radians(lat2)) * np.sin(np.radians(lon2))
        z2 = sat_r * np.sin(np.radians(lat2))
        
        return np.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

    def update_satellite_position(self, sat_id: int, lat: float, lon: float):
        with self.connection_lock:
            if sat_id not in self.satellites:
                self.satellites[sat_id] = ISLNode(sat_id, lat, lon)
                logging.info(f"Satellite {sat_id} added to the network at lat={lat:.2f}, lon={lon:.2f}.")
            else:
                self.satellites[sat_id].lat = lat
                self.satellites[sat_id].lon = lon
                self.satellites[sat_id].last_update = time.time()
                logging.info(f"Satellite {sat_id} updated position to lat={lat:.2f}, lon={lon:.2f}.")
            
            self.update_neighbors(sat_id)
            self.update_routing_tables()

    def update_neighbors(self, sat_id: int):
        sat = self.satellites[sat_id]
        sat.neighbors.clear()
        
        for other_id, other_sat in self.satellites.items():
            if other_id != sat_id:
                distance = self.calculate_distance(
                    sat.lat, sat.lon,
                    other_sat.lat, other_sat.lon
                )
                if distance <= self.max_isl_distance:
                    sat.neighbors[other_id] = (other_sat.lat, other_sat.lon)
        
        if sat.neighbors:
            logging.info(f"Satellite {sat_id} neighbors: {list(sat.neighbors.keys())}.")
        else:
            logging.warning(f"Satellite {sat_id} has no neighbors within distance {self.max_isl_distance} km.")

    def update_routing_tables(self):
        for source_id in self.satellites:
            self.satellites[source_id].routing_table = self._dijkstra(source_id)
            if self.satellites[source_id].routing_table:
                logging.info(f"Routing table for satellite {source_id}: {self.satellites[source_id].routing_table}.")
            else:
                logging.warning(f"Routing table for satellite {source_id} is empty.")
                
    def _dijkstra(self, source_id: int) -> Dict[int, int]:
        distances = {sat_id: float('inf') for sat_id in self.satellites}
        distances[source_id] = 0
        previous = {sat_id: None for sat_id in self.satellites}
        unvisited = set(self.satellites.keys())
        
        while unvisited:
            current = min(unvisited, key=lambda sat_id: distances[sat_id])
            if distances[current] == float('inf'):
                break  # Remaining nodes are unreachable
                
            unvisited.remove(current)
            
            for neighbor_id in self.satellites[current].neighbors:
                if neighbor_id in unvisited:
                    distance = self.calculate_distance(
                        self.satellites[current].lat,
                        self.satellites[current].lon,
                        self.satellites[neighbor_id].lat,
                        self.satellites[neighbor_id].lon
                    )
                    alt_distance = distances[current] + distance
                    if alt_distance < distances[neighbor_id]:
                        distances[neighbor_id] = alt_distance
                        previous[neighbor_id] = current
        
        routing_table = {}
        for dest_id in self.satellites:
            if dest_id != source_id and previous[dest_id] is not None:
                next_hop = dest_id
                while previous[next_hop] != source_id:
                    next_hop = previous[next_hop]
                routing_table[dest_id] = next_hop
        
        return routing_table

    def get_next_hop(self, source_id: int, dest_id: int) -> int:
        with self.connection_lock:
            if source_id in self.satellites and dest_id in self.satellites[source_id].routing_table:
                return self.satellites[source_id].routing_table[dest_id]
        return None

def keep_moving(global_dequeue, orbit_z_axis, num_sats, velocity, sat_index, isl_network):
    from movement_simulation import init_satellites, satellites_move  # Import here to avoid circular imports
    
    sat_ll_list = init_satellites(orbit_z_axis, num_sats)
    (lat, lon) = sat_ll_list[sat_index]
    start_time = time.time()
    
    while True:
        time.sleep(1)
        end_time = time.time()
        t = end_time - start_time
        start_time = end_time
        
        lat, lon = satellites_move((lat, lon), orbit_z_axis, velocity, t)
        print(f"Satellite {sat_index} position: lat {lat}, lon {lon}")
        
        # Update position in ISL network
        isl_network.update_satellite_position(sat_index, lat, lon)
        
        # Update global queue
        global_dequeue.append((lat, lon))
        
        # Print ISL status only when there are connections or routes
        if sat_index in isl_network.satellites:
            sat = isl_network.satellites[sat_index]
            if sat.neighbors:
                print(f"Connected to satellites: {list(sat.neighbors.keys())}")
            if sat.routing_table:
                print(f"Routing table: {sat.routing_table}")

def server(global_dequeue, server_addr, buffer_size, sat_node_number, isl_network):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_addr)
    print(f"Satellite {sat_node_number} listening on {server_addr[0]}:{server_addr[1]}...")
    
    received_packets = {}
    
    while True:
        data, client_address = server_socket.recvfrom(buffer_size)
        print(f"Received packet from {client_address}")
        
        # Decode packet header
        flag = int.from_bytes(data[:4], 'big')
        node_number = int.from_bytes(data[4:8], 'big')
        
        # Handle location inquiry
        if flag == 0:
            try:
                lat, lon = global_dequeue.pop()
            except IndexError:
                lat, lon = -800, -800
                
            lat_info = int(lat).to_bytes(4, 'big', signed=True)
            lon_info = int(lon).to_bytes(4, 'big', signed=True)
            ll_info = flag.to_bytes(4, 'big') + sat_node_number.to_bytes(4, 'big') + lat_info + lon_info
            server_socket.sendto(ll_info, client_address)
            continue

        # Handle data packet
        packet_number = int.from_bytes(data[8:12], 'big')
        total_packets = int.from_bytes(data[12:16], 'big')
        chunk = data[16:]
        
        # Check if this packet needs to be forwarded through ISL
        next_hop = isl_network.get_next_hop(sat_node_number, node_number)
        
        if next_hop is not None:
            # Forward packet through ISL
            next_hop_addr = ('localhost', 8080 + next_hop)  # Assuming sequential port numbers
            print(f"Forwarding packet to satellite {next_hop} at {next_hop_addr}")
            server_socket.sendto(data, next_hop_addr)
            
            # Send acknowledgment to original sender
            ack = flag.to_bytes(4, 'big') + sat_node_number.to_bytes(4, 'big') + packet_number.to_bytes(4, 'big')
            server_socket.sendto(ack, client_address)
        else:
            # Process packet locally
            if node_number not in received_packets:
                received_packets[node_number] = {}
            received_packets[node_number][packet_number] = chunk
            
            # Send acknowledgment
            ack = flag.to_bytes(4, 'big') + sat_node_number.to_bytes(4, 'big') + packet_number.to_bytes(4, 'big')
            server_socket.sendto(ack, client_address)
            
            # Check if all packets received
            if len(received_packets[node_number]) == total_packets:
                print(f"All packets from node {node_number} received!")
                binary_stream = b''.join(received_packets[node_number][i] for i in range(total_packets))
                original_string = binary_stream.decode()
                print("Reconstructed String:", original_string)

if __name__ == "__main__":
    # Configuration
    global_dequeue = deque(maxlen=10)
    NUM_SATS = 5
    SAT_INDEX = 0
    SAT_NODE_NUM = 1
    ORBIT_Z_AXIS = (0, 0)
    VELOCITY = 27000/111.3/(60*60)  # degrees per second
    SERVER_ADDR = ('10.35.70.31', 8081)
    BUFFER_SIZE = 1024
    
    # Initialize ISL network
    isl_network = InterSatelliteLinks(NUM_SATS)
    
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