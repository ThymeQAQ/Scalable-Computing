import subprocess
import socket
import time
import numpy as np
import threading
import psutil
from datetime import datetime
from typing import Dict, Optional, Tuple

class EarthStation:
    def __init__(self, lat: float, lon: float, node_num: int):
        self.lat = lat
        self.lon = lon
        self.node_num = node_num
        self.connected_satellite = None
        self.best_distance = float('inf')
        self.connection_history = []
        self.connection_start_time = None
        self.total_data_sent = 0
        self.successful_transmissions = 0
        
    def find_best_satellite(self, satellite_positions: Dict[int, Tuple[float, float]]) -> Optional[int]:
        """Find the closest satellite to connect to"""
        best_satellite = None
        best_distance = float('inf')
        
        for sat_id, (sat_lat, sat_lon) in satellite_positions.items():
            distance = earth_sat_distance(self.lat, self.lon, sat_lat, sat_lon)
            if distance < best_distance:
                best_distance = distance
                best_satellite = sat_id
        
        # Record handover if satellite changes
        if best_satellite != self.connected_satellite:
            if self.connected_satellite is not None:
                handover_time = time.time()
                duration = handover_time - (self.connection_start_time or handover_time)
                self.connection_history.append({
                    'satellite': self.connected_satellite,
                    'start_time': self.connection_start_time,
                    'end_time': handover_time,
                    'duration': duration,
                    'data_sent': self.total_data_sent,
                    'successful_transmissions': self.successful_transmissions
                })
                print(f"\n=== Handover Event ===")
                print(f"Previous Satellite: {self.connected_satellite}")
                print(f"New Satellite: {best_satellite}")
                print(f"Connection Duration: {duration:.2f}s")
                print(f"Data Sent: {self.total_data_sent} bytes")
                print(f"Successful Transmissions: {self.successful_transmissions}")
                print("===================\n")
                
                # Reset counters for new connection
                self.total_data_sent = 0
                self.successful_transmissions = 0
            
            self.connected_satellite = best_satellite
            self.connection_start_time = time.time()
                
        self.best_distance = best_distance
        return best_satellite

def earth_sat_distance(earth_lat: float, earth_lon: float, sat_lat: float, sat_lon: float) -> float:
    """Calculate the distance between earth station and satellite"""
    SAT_H = 550.
    EARTH_R = 6378.
    
    earth_lat, earth_lon = np.radians(earth_lat), np.radians(earth_lon)
    sat_lat, sat_lon = np.radians(sat_lat), np.radians(sat_lon)
    
    dlat = sat_lat - earth_lat
    dlon = sat_lon - earth_lon
    a = np.sin(dlat/2)**2 + np.cos(earth_lat) * np.cos(sat_lat) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    
    ground_distance = EARTH_R * c
    distance = np.sqrt(ground_distance**2 + SAT_H**2)
    return distance

def query_satellite_network(socket: socket.socket, server_addr: Tuple[str, int], 
                          buffer_size: int, timeout: float) -> Dict[int, Tuple[float, float]]:
    """Query all satellites in the network for their positions"""
    satellite_positions = {}
    
    for port in range(8081, 8086):  # Assuming 5 satellites
        try:
            current_addr = (server_addr[0], port)
            flag = 0
            node_num = 0
            header = flag.to_bytes(4, 'big') + node_num.to_bytes(4, 'big') + \
                    (0).to_bytes(4, 'big') + (0).to_bytes(4, 'big')
            inquiry = header + (0).to_bytes(4, 'big')
            
            socket.sendto(inquiry, current_addr)
            ack, _ = socket.recvfrom(buffer_size)
            
            flag = int.from_bytes(ack[:4], 'big')
            sat_id = int.from_bytes(ack[4:8], 'big')
            sat_lat = int.from_bytes(ack[8:12], 'big', signed=True)
            sat_lon = int.from_bytes(ack[12:16], 'big', signed=True)
            
            satellite_positions[sat_id] = (sat_lat, sat_lon)
            
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error querying satellite at port {port}: {e}")
            
    return satellite_positions

class NetworkMonitor:
    def __init__(self):
        self.packet_loss_window = []
        self.latency_window = []
        self.window_size = 10
        self.last_report_time = time.time()
        self.report_interval = 5  # seconds
        
    def update_metrics(self, rtt: float, success: bool):
        self.latency_window.append(rtt if success else float('inf'))
        self.packet_loss_window.append(1 if success else 0)
        
        if len(self.latency_window) > self.window_size:
            self.latency_window.pop(0)
        if len(self.packet_loss_window) > self.window_size:
            self.packet_loss_window.pop(0)
            
        current_time = time.time()
        if current_time - self.last_report_time >= self.report_interval:
            self.report_metrics()
            self.last_report_time = current_time
            
    def report_metrics(self):
        if not self.latency_window:
            return
            
        success_rate = sum(self.packet_loss_window) / len(self.packet_loss_window) * 100
        valid_latencies = [lat for lat in self.latency_window if lat != float('inf')]
        avg_latency = sum(valid_latencies) / len(valid_latencies) if valid_latencies else float('inf')
        
        print(f"\n=== Network Status Report ===")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Average Latency: {avg_latency:.2f}ms")
        print("==========================\n")

def client(server_addr: Tuple[str, int], buffer_size: int, timeout: float, 
          debug_interval: float, chunk_size: int, earth_station: EarthStation):
    message = "This is a test string that will be sent as binary data over UDP in smaller packets."
    binary_stream = message.encode('utf-8')
    chunks = [binary_stream[i:i + chunk_size] for i in range(0, len(binary_stream), chunk_size)]
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)
    
    network_monitor = NetworkMonitor()

    while True:
        try:
            # Query satellite network
            satellite_positions = query_satellite_network(client_socket, server_addr, buffer_size, timeout)
            if not satellite_positions:
                print("No satellites available. Retrying...")
                time.sleep(debug_interval)
                continue
            
            # Find best satellite
            best_sat = earth_station.find_best_satellite(satellite_positions)
            if best_sat is None:
                print("Cannot find suitable satellite. Retrying...")
                time.sleep(debug_interval)
                continue
            
            # Use the port of the best satellite
            current_addr = (server_addr[0], 8080 + best_sat)
            
            # Send data chunks
            for packet_number, chunk in enumerate(chunks):
                success = False
                retries = 0
                max_retries = 3
                
                while not success and retries < max_retries:
                    try:
                        start_time = time.time()
                        
                        # Prepare and send packet
                        flag = 1
                        header = flag.to_bytes(4, 'big') + earth_station.node_num.to_bytes(4, 'big') + \
                                packet_number.to_bytes(4, 'big') + len(chunks).to_bytes(4, 'big')
                        packet = header + chunk
                        
                        client_socket.sendto(packet, current_addr)
                        earth_station.total_data_sent += len(packet)
                        
                        # Wait for acknowledgment
                        ack, _ = client_socket.recvfrom(buffer_size)
                        end_time = time.time()
                        
                        rtt = (end_time - start_time) * 1000
                        earth_station.successful_transmissions += 1
                        success = True
                        
                        # Update network metrics
                        network_monitor.update_metrics(rtt, True)
                        
                    except socket.timeout:
                        retries += 1
                        network_monitor.update_metrics(float('inf'), False)
                        print(f"Timeout: packet={packet_number}, retry={retries}")
                    except Exception as e:
                        print(f"Error sending packet {packet_number}: {e}")
                        break
                        
                    time.sleep(debug_interval)
                
            time.sleep(5)  # Wait before next transmission
            
        except Exception as e:
            print(f"Error in client loop: {e}")
            time.sleep(debug_interval)

if __name__ == "__main__":
    SERVER_ADDR = ('localhost', 8081)
    BUFFER_SIZE = 1024
    EARTH_LL = (0, -180)
    EARTH_NODE_NUM = 10
    TIMEOUT = 2
    DEBUG_INTER = 0.5
    CHUNK_SIZE = 10
    
    earth_station = EarthStation(EARTH_LL[0], EARTH_LL[1], EARTH_NODE_NUM)
    
    client_thread = threading.Thread(
        target=client,
        args=(SERVER_ADDR, BUFFER_SIZE, TIMEOUT, DEBUG_INTER, CHUNK_SIZE, earth_station),
        daemon=True
    )
    
    client_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n=== Final Connection Statistics ===")
        for conn in earth_station.connection_history:
            print(f"\nSatellite {conn['satellite']}:")
            print(f"Duration: {conn['duration']:.2f}s")
            print(f"Data Sent: {conn['data_sent']} bytes")
            print(f"Successful Transmissions: {conn['successful_transmissions']}")
        print("\nExiting..")