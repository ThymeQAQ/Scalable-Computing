import subprocess
import socket
import time
import numpy as np
import threading
import psutil

class EarthStation:
    def __init__(self, lat: float, lon: float, node_num: int):
        self.lat = lat
        self.lon = lon
        self.node_num = node_num
        self.connected_satellite = None
        self.best_distance = float('inf')

    def find_best_satellite(self, satellite_positions):
        """Find the closest satellite to connect to"""
        best_satellite = None
        best_distance = float('inf')
        
        for sat_id, (sat_lat, sat_lon) in satellite_positions.items():
            distance = earth_sat_distance(self.lat, self.lon, sat_lat, sat_lon)
            if distance < best_distance:
                best_distance = distance
                best_satellite = sat_id
                
        self.connected_satellite = best_satellite
        self.best_distance = best_distance
        return best_satellite

def start_clumsy(single_latency, single_drop_rate):
    CLUM_DIR = "clumsy"
    cmd = f"clumsy.exe --drop on --drop-inbound on --drop-outbound on --drop-chance {single_drop_rate} " \
          f"--lag on --lag-inbound on --lag-outbound on --lag-time {single_latency}"
    process = subprocess.Popen(cmd, cwd=CLUM_DIR, shell=True)
    print("clumsy started.")
    return process.pid

def kill_clumsy(pid):
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.kill()
    parent.kill()
    print("clumsy stopped.")

def earth_sat_distance(earth_lat, earth_lon, sat_lat, sat_lon):
    SAT_H = 550.
    EARTH_R = 6378.
    
    # Convert to radians
    earth_lat, earth_lon = np.radians(earth_lat), np.radians(earth_lon)
    sat_lat, sat_lon = np.radians(sat_lat), np.radians(sat_lon)
    
    # Calculate using haversine formula
    dlat = sat_lat - earth_lat
    dlon = sat_lon - earth_lon
    a = np.sin(dlat/2)**2 + np.cos(earth_lat) * np.cos(sat_lat) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    # Calculate ground distance
    ground_distance = EARTH_R * c
    
    # Calculate actual 3D distance considering satellite altitude
    distance = np.sqrt(ground_distance**2 + SAT_H**2)
    return distance

def e2s_lantency(earth_lat, earth_lon, sat_lat, sat_lon):
    LIGHT_V = 300000.  # km/s
    distance = earth_sat_distance(earth_lat, earth_lon, sat_lat, sat_lon)
    single_bound_lantency = distance/LIGHT_V
    return single_bound_lantency*1000  # return in milliseconds

def e2s_packet_loss(earth_lat, earth_lon, sat_lat, sat_lon):
    SAT_H = 550.
    distance = earth_sat_distance(earth_lat, earth_lon, sat_lat, sat_lon)
    single_bound_loss_rate = min(0.02*np.exp((distance-SAT_H)/1000.), 1.0)
    return single_bound_loss_rate*100

def query_satellite_network(socket, server_addr, buffer_size, timeout):
    """Query all satellites in the network for their positions"""
    satellite_positions = {}
    
    # Try different ports for different satellites
    for port in range(8081, 8086):  # Assuming 5 satellites
        try:
            current_addr = (server_addr[0], port)
            flag = 0
            node_num = 0  # Use 0 for position queries
            header = flag.to_bytes(4, 'big') + node_num.to_bytes(4, 'big') + \
                    (0).to_bytes(4, 'big') + (0).to_bytes(4, 'big')
            inquiry = header + (0).to_bytes(4, 'big')
            
            socket.sendto(inquiry, current_addr)
            ack, _ = socket.recvfrom(buffer_size)
            
            # Decode satellite position
            flag = int.from_bytes(ack[:4], 'big')
            sat_id = int.from_bytes(ack[4:8], 'big')
            sat_lat = int.from_bytes(ack[8:12], 'big', signed=True)
            sat_lon = int.from_bytes(ack[12:16], 'big', signed=True)
            
            satellite_positions[sat_id] = (sat_lat, sat_lon)
            print(f"Found satellite {sat_id} at lat={sat_lat}, lon={sat_lon}")
            
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error querying satellite at port {port}: {e}")
            
    return satellite_positions

def clumsy_simulate(server_addr, buffer_size, timeout, earth_station):
    inquire_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inquire_socket.settimeout(timeout)
    clumsy_pid = None
    
    while True:
        try:
            # Query all satellites in the network
            satellite_positions = query_satellite_network(inquire_socket, server_addr, buffer_size, timeout)
            
            if satellite_positions:
                # Find best satellite to connect to
                best_sat = earth_station.find_best_satellite(satellite_positions)
                if best_sat is not None:
                    sat_lat, sat_lon = satellite_positions[best_sat]
                    
                    # Calculate network conditions
                    distance = earth_sat_distance(earth_station.lat, earth_station.lon, sat_lat, sat_lon)
                    single_latency = e2s_lantency(earth_station.lat, earth_station.lon, sat_lat, sat_lon)
                    single_drop_rate = e2s_packet_loss(earth_station.lat, earth_station.lon, sat_lat, sat_lon)
                    
                    print(f"\nConnected to Satellite {best_sat}:")
                    print(f"Earth station: lat={earth_station.lat}, lon={earth_station.lon}")
                    print(f"Satellite: lat={sat_lat}, lon={sat_lon}")
                    print(f"Distance: {distance:.2f} km")
                    print(f"Latency: {single_latency:.2f} ms")
                    print(f"Packet loss: {single_drop_rate:.2f}%")
                    
                    # Update clumsy simulation
                    if clumsy_pid is not None:
                        kill_clumsy(clumsy_pid)
                    clumsy_pid = start_clumsy(single_latency, single_drop_rate)
            
        except Exception as e:
            print(f"Error in clumsy simulation: {e}")
            
        time.sleep(3)

def client(server_addr, buffer_size, timeout, debug_interval, chunk_size, earth_station):
    message = "This is a test string that will be sent as binary data over UDP in smaller packets."
    binary_stream = message.encode('utf-8')
    chunks = [binary_stream[i:i + chunk_size] for i in range(0, len(binary_stream), chunk_size)]
    total_packets = len(chunks)
    total_send = 0
    rtts = []

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)

    while True:
        # Query satellite network before sending data
        satellite_positions = query_satellite_network(client_socket, server_addr, buffer_size, timeout)
        if not satellite_positions:
            print("No satellites available. Retrying...")
            time.sleep(debug_interval)
            continue
            
        # Find best satellite to connect to
        best_sat = earth_station.find_best_satellite(satellite_positions)
        if best_sat is None:
            print("Cannot find suitable satellite. Retrying...")
            time.sleep(debug_interval)
            continue
            
        # Use the port of the best satellite
        current_addr = (server_addr[0], 8080 + best_sat)
        print(f"\nSending through Satellite {best_sat} (udp://{current_addr[0]}:{current_addr[1]}) with {total_packets} packets:")

        for packet_number, chunk in enumerate(chunks):
            flag = 1
            header = flag.to_bytes(4, 'big') + earth_station.node_num.to_bytes(4, 'big') + \
                    packet_number.to_bytes(4, 'big') + total_packets.to_bytes(4, 'big')
            packet = header + chunk
            
            while True:
                try:
                    total_send += 1
                    start_time = time.time()
                    client_socket.sendto(packet, current_addr)
                    ack, _ = client_socket.recvfrom(buffer_size)
                    end_time = time.time()
                    
                    rtt = (end_time - start_time) * 1000
                    rtts.append(rtt)
                    ack_flag = int.from_bytes(ack[:4], 'big')
                    ack_node = int.from_bytes(ack[4:8], 'big')
                    ack_packet = int.from_bytes(ack[8:12], 'big')
                    
                    print(f"Received ACK from Satellite {ack_node}: packet={ack_packet}, RTT={rtt:.2f} ms")
                    break
                    
                except socket.timeout:
                    print(f"Timeout: packet={packet_number}, resending...")
                except Exception as e:
                    print(f"Error sending packet {packet_number}: {e}")
                time.sleep(debug_interval)
                
            time.sleep(debug_interval)

        # Print statistics
        print(f"\n--- Statistics for connection through Satellite {best_sat} ---")
        if rtts:
            print(f"Packets: sent={total_send}, received={len(rtts)}, lost={total_send-len(rtts)}")
            print(f"Loss rate: {((total_send-len(rtts))/total_send*100):.1f}%")
            print(f"RTT: min={min(rtts):.2f}ms, avg={sum(rtts)/len(rtts):.2f}ms, max={max(rtts):.2f}ms")
        
        time.sleep(5)  # Wait before starting next transmission

if __name__ == "__main__":
    SERVER_ADDR = ('localhost', 8081)  # Base address, actual ports will be 8081-8085
    BUFFER_SIZE = 1024
    EARTH_LL = (0, -180)  # latitude, longitude
    EARTH_NODE_NUM = 10
    TIMEOUT = 2  # 2s timeout
    DEBUG_INTER = 1  # 1s
    CHUNK_SIZE = 10  # bits
    
    # Create earth station object
    earth_station = EarthStation(EARTH_LL[0], EARTH_LL[1], EARTH_NODE_NUM)
    
    # Create and start threads
    clumsy_thread = threading.Thread(
        target=clumsy_simulate,
        args=(SERVER_ADDR, BUFFER_SIZE, TIMEOUT, earth_station),
        daemon=True
    )
    
    client_thread = threading.Thread(
        target=client,
        args=(SERVER_ADDR, BUFFER_SIZE, TIMEOUT, DEBUG_INTER, CHUNK_SIZE, earth_station),
        daemon=True
    )
    
    clumsy_thread.start()
    client_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting..")