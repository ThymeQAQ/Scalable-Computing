import math
import time
import threading
import socket
import requests
import selectors
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
import json
from ground_station import GroundStationManager
from config import OrbitalConfig, NetworkConfig, SimulationConfig

@dataclass
class Position:
    latitude: float
    longitude: float
    altitude: float  # in kilometers
    timestamp: float

    def to_dict(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "timestamp": self.timestamp
        }

class SatelliteStatus(Enum):
    ACTIVE = "active"
    HANDOVER = "handover"
    OFFLINE = "offline"

class HandoverState:
    def __init__(self):
        self.is_handover = False
        self.target_peer_id = None
        self.start_time = None
        self.timeout = 30  # seconds
        self.lock = threading.Lock()

class LEOSatelliteNode:
    def __init__(self, node_id: str, host: str, port: int, 
                 initial_position: Position,
                 orbital_period: float = 90,
                 max_connections: int = 5,
                 registry_url: str = "http://localhost:5000"):
        
        self.node_id = node_id
        self.host = host
        self.port = port
        self.position = initial_position
        self.orbital_period = orbital_period
        self.max_connections = max_connections
        self.registry_url = registry_url
        
        self.status = SatelliteStatus.ACTIVE
        self.peers: Dict[str, dict] = {}
        self.connections: Dict[str, socket.socket] = {}
        self.received_broadcasts: set = set()
        
        self.is_running = True
        self._lock = threading.Lock()
        
        # Initialize networking
        self.selector = selectors.DefaultSelector()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Handover management
        self.handover_state = HandoverState()
        self.handover_threshold = 1000 
    
        
        # Statistics
        self.connection_stats = {
            'active_connections': 0,
            'total_bytes_sent': 0,
            'total_bytes_received': 0,
            'average_latency': 0.0
        }
        
        self.threads = []
        self.ground_station_manager = GroundStationManager()
        self.connected_ground_stations = set()
        self.config = {
            'orbital': OrbitalConfig(),
            'network': NetworkConfig(
                max_connections=max_connections,
                registry_url=registry_url
            ),
            'simulation': SimulationConfig()
        }

    def start(self):
        """Start the satellite node and all its background processes"""
        try:
            # Bind and listen on the specified port
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.setblocking(False)
            
            # Register server socket with selector
            self.selector.register(
                self.server_socket,
                selectors.EVENT_READ,
                data=None
            )
            
            # Start background tasks
            self._start_background_tasks()
            
            # Start main network event loop
            self.network_thread = threading.Thread(target=self._network_loop)
            self.network_thread.daemon = True
            self.network_thread.start()
            self.threads.append(self.network_thread)
            
            print(f"[INFO] Satellite {self.node_id} started successfully")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to start satellite node: {e}")
            self.stop()
            raise

    def _start_background_tasks(self):
        """Start all background maintenance threads"""
        tasks = [
            self._update_position_loop,
            self._discover_peers_loop,
            self._broadcast_status_loop,
            self._cleanup_loop,
            self.update_ground_station_connections
        ]
        
        for task in tasks:
            thread = threading.Thread(target=task)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def update_ground_station_connections(self):
        """Update connections to ground stations based on visibility"""
        visible_stations = self.ground_station_manager.get_visible_stations(
            self.position.latitude,
            self.position.longitude
        )
        
        # Update connected stations
        self.connected_ground_stations = {
            station.station_id for station in visible_stations
        }
        
        # Update last contact for visible stations
        for station in visible_stations:
            station.update_contact()

    def _update_position_loop(self):
        """Continuously update satellite position based on orbital parameters"""
        while self.is_running:
            current_time = time.time()
            
            # Calculate orbital position
            orbit_progress = (current_time % (self.orbital_period * 60)) / (self.orbital_period * 60)
            
            # Update position using realistic orbital mechanics (simplified)
            self.position.longitude = (orbit_progress * 360 - 180) % 360
            self.position.latitude = 53.0 * math.sin(2 * math.pi * orbit_progress)
            self.position.timestamp = current_time
            
            self._update_registry()
            time.sleep(1)

    def _network_loop(self):
        """Main network event loop"""
        while self.is_running:
            try:
                events = self.selector.select(timeout=1)
                for key, mask in events:
                    if key.data is None:
                        self._accept_connection(key.fileobj)
                    else:
                        self._handle_connection(key, mask)
            except Exception as e:
                print(f"[ERROR] Network loop error: {e}")
                continue

    def _accept_connection(self, sock):
        """Accept new connection and register it with selector"""
        try:
            conn, addr = sock.accept()
            conn.setblocking(False)
            
            if len(self.connections) >= self.max_connections:
                conn.close()
                return
            
            # Register new connection for read/write events
            self.selector.register(
                conn,
                selectors.EVENT_READ | selectors.EVENT_WRITE,
                data={'addr': addr, 'inb': b'', 'outb': b'', 'peer_id': None}
            )
            
            with self._lock:
                self.connection_stats['active_connections'] += 1
                
        except Exception as e:
            print(f"[ERROR] Failed to accept connection: {e}")

    def _handle_connection(self, key, mask):
        """Handle events on existing connections"""
        sock = key.fileobj
        data = key.data
        
        try:
            if mask & selectors.EVENT_READ:
                recv_data = sock.recv(4096)
                if recv_data:
                    data['inb'] += recv_data
                    self._process_received_data(sock, data)
                else:
                    self._close_connection(sock)
                    
            if mask & selectors.EVENT_WRITE:
                if data['outb']:
                    sent = sock.send(data['outb'])
                    data['outb'] = data['outb'][sent:]
                    
                    with self._lock:
                        self.connection_stats['total_bytes_sent'] += sent
                    
        except Exception as e:
            print(f"[ERROR] Connection handler error: {e}")
            self._close_connection(sock)

    def _discover_peers_loop(self):
        """Periodically discover and update peer information from registry"""
        while self.is_running:
            try:
                response = requests.get(f"{self.registry_url}/nodes")
                if response.status_code == 200:
                    nodes = response.json()
                    with self._lock:
                        # Update peers dictionary excluding self
                        self.peers = {
                            node_id: data 
                            for node_id, data in nodes.items() 
                            if node_id != self.node_id
                        }
                        self._connect_to_new_peers()
                
            except Exception as e:
                print(f"[ERROR] Peer discovery failed: {e}")
            
            time.sleep(5)

    def _connect_to_new_peers(self):
        """Establish connections with newly discovered peers"""
        for peer_id, peer_data in self.peers.items():
            if not any(d.get('peer_id') == peer_id for d in 
                      [key.data for key in self.selector.get_map().values() if key.data]):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.setblocking(False)
                    sock.connect_ex((peer_data['node_ip'], peer_data['node_port']))
                    
                    self.selector.register(
                        sock,
                        selectors.EVENT_READ | selectors.EVENT_WRITE,
                        data={'addr': (peer_data['node_ip'], peer_data['node_port']),
                              'inb': b'', 'outb': b'', 'peer_id': peer_id}
                    )
                    print(f"[INFO] Connected to peer {peer_id}")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to connect to peer {peer_id}: {e}")

    def _broadcast_status_loop(self):
        """Periodically broadcast status to all connected peers"""
        while self.is_running:
            try:
                status_message = {
                    "message_id": f"{self.node_id}_{time.time()}",
                    "sender_id": self.node_id,
                    "type": "STATUS",
                    "position": self.position.to_dict(),
                    "status": self.status.value,
                    "timestamp": time.time()
                }
                
                self._broadcast_message(status_message)
                time.sleep(2)
                
            except Exception as e:
                print(f"[ERROR] Status broadcast failed: {e}")

    def _broadcast_message(self, message: dict):
        """Broadcast message to all connected peers except self"""
        message_json = json.dumps(message)
        message_bytes = message_json.encode()
        length_prefix = len(message_bytes).to_bytes(8, byteorder='big')
        
        # Get all connections except the sender
        for key in self.selector.get_map().values():
            if key.data and key.data.get('peer_id') != message.get('sender_id'):
                try:
                    key.data['outb'] += length_prefix + message_bytes
                except Exception as e:
                    print(f"[ERROR] Failed to queue broadcast: {e}")

    def _process_received_data(self, sock, data):
        """Process received data and handle complete messages"""
        while len(data['inb']) >= 8:
            msg_len = int.from_bytes(data['inb'][:8], byteorder='big')
            if len(data['inb']) < msg_len + 8:
                break
                
            msg_data = data['inb'][8:msg_len+8]
            data['inb'] = data['inb'][msg_len+8:]
            
            try:
                message = json.loads(msg_data.decode())
                self._handle_message(message)
                
                with self._lock:
                    self.connection_stats['total_bytes_received'] += msg_len
                    
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to decode message: {e}")

    def _handle_message(self, message: dict):
        """Handle different types of messages"""
        message_id = message.get("message_id")
        
        # Skip if we've already seen this message
        if message_id in self.received_broadcasts:
            return
            
        self.received_broadcasts.add(message_id)
        
        # Process based on message type
        if message["type"] == "STATUS":
            self._handle_status_update(message)
            # Rebroadcast to other peers
            self._broadcast_message(message)
        else:
            print(f"[WARNING] Unknown message type: {message.get('type')}")

    def _handle_status_update(self, message: dict):
        """Handle status update from peer"""
        peer_id = message["sender_id"]
        if peer_id != self.node_id:
            self.peers[peer_id] = {
                "position": message["position"],
                "status": message["status"],
                "last_seen": time.time()
            }

    def _cleanup_loop(self):
        """Periodically clean up old data and dead connections"""
        while self.is_running:
            current_time = time.time()
            
            # Clean up old received broadcast IDs
            self.received_broadcasts = {
                msg_id for msg_id in self.received_broadcasts
                if float(msg_id.split('_')[1]) > current_time - 60
            }
            
            # Clean up dead peers
            with self._lock:
                dead_peers = [
                    peer_id for peer_id, data in self.peers.items()
                    if current_time - data.get("last_seen", 0) > 30
                ]
                for peer_id in dead_peers:
                    self.peers.pop(peer_id, None)
            
            time.sleep(30)

    def _update_registry(self):
        """Update position information in registry server"""
        try:
            data = {
                "node_id": self.node_id,
                "node_ip": self.host,
                "node_port": self.port,
                "position": self.position.to_dict()
            }
            
            response = requests.post(f"{self.registry_url}/register", json=data)
            if response.status_code != 201:
                print(f"[WARNING] Failed to update registry: {response.text}")
                
        except Exception as e:
            print(f"[ERROR] Registry update failed: {e}")

    def _close_connection(self, sock):
        """Clean up and close a connection"""
        try:
            self.selector.unregister(sock)
            sock.close()
            
            with self._lock:
                self.connection_stats['active_connections'] -= 1
                
        except Exception as e:
            print(f"[ERROR] Error closing connection: {e}")

    def stop(self):
        """Stop the satellite node and cleanup"""
        self.is_running = False
        
        # Close all connections
        for key in list(self.selector.get_map().values()):
            if key.fileobj is not self.server_socket:
                self._close_connection(key.fileobj)
        
        # Close server socket
        try:
            self.server_socket.close()
            self.selector.close()
        except:
            pass
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=1.0)

if __name__ == "__main__":
    # Example usage
    initial_position = Position(
        latitude=0.0,
        longitude=0.0,
        altitude=550.0,
        timestamp=time.time()
    )
    
    satellite = LEOSatelliteNode(
        node_id="sat1",
        host="localhost",
        port=8001,
        initial_position=initial_position
    )
    
    try:
        satellite.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down satellite...")
        satellite.stop()