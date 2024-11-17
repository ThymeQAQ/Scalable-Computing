from dataclasses import dataclass
from typing import Dict, List, Optional
import random
import time
import threading
import math
import json
from message import Message, MessageType

@dataclass
class SatelliteMetrics:
    connection_quality: float  # 0-1.0
    traffic_load: float  # 0-1.0
    signal_strength: float  # 0-1.0
    interference_level: float  # 0-1.0
    battery_level: float  # 0-100
    temperature: float  # in Celsius

class SatelliteMonitor:
    def __init__(self, satellite):
        self.satellite = satellite
        self.neighbors: Dict[str, Dict] = {}  # Stores neighbor satellites' status
        self.metrics = SatelliteMetrics(
            connection_quality=1.0,
            traffic_load=0.0,
            signal_strength=1.0,
            interference_level=0.0,
            battery_level=100.0,
            temperature=20.0
        )
        
        # Environmental simulation parameters
        self.config = satellite.config
        self.weather_conditions = self.config['simulation'].weather_conditions
        self.current_weather = 'clear'
        
        # Start monitoring threads
        self.start_monitoring()

    def start_monitoring(self):
        """Start all monitoring and simulation threads"""
        threads = [
            threading.Thread(target=self.broadcast_status_loop),
            threading.Thread(target=self.simulate_metrics_loop),
            threading.Thread(target=self.check_handover_loop)
        ]
        
        for thread in threads:
            thread.daemon = True
            thread.start()

    def broadcast_status_loop(self):
        """Periodically broadcast satellite status to all neighbors"""
        while self.satellite.is_running:
            try:
                status_message = self.create_status_message()
                self.broadcast_status(status_message)
                time.sleep(2)  # Broadcast every 2 seconds
            except Exception as e:
                print(f"[ERROR] Status broadcast error: {e}")

    def create_status_message(self) -> Message:
        """Create a status message with current satellite information"""
        return Message(
            sender_id=self.satellite.node_id,
            message_type=MessageType.BROADCAST,
            content={
                'position': {
                    'latitude': self.satellite.position.latitude,
                    'longitude': self.satellite.position.longitude,
                    'altitude': self.satellite.position.altitude
                },
                'status': self.satellite.status.value,
                'metrics': {
                    'connection_quality': self.metrics.connection_quality,
                    'traffic_load': self.metrics.traffic_load,
                    'signal_strength': self.metrics.signal_strength,
                    'interference_level': self.metrics.interference_level,
                    'battery_level': self.metrics.battery_level,
                    'temperature': self.metrics.temperature
                },
                'timestamp': time.time()
            }
        )

    def broadcast_status(self, message: Message):
        """Broadcast status message to all connected nodes"""
        message_json = message.to_json()
        message_bytes = message_json.encode()
        message_length = len(message_bytes).to_bytes(8, byteorder='big')
        
        with self.satellite._lock:
            for node_id, conn in self.satellite.connections.items():
                try:
                    conn.sendall(message_length + message_bytes)
                except Exception as e:
                    print(f"[ERROR] Failed to send status to {node_id}: {e}")

    def simulate_metrics_loop(self):
        """Simulate environmental conditions and their effects on metrics"""
        while self.satellite.is_running:
            try:
                self.simulate_weather_changes()
                self.simulate_traffic_load()
                self.simulate_battery_drain()
                self.simulate_temperature()
                self.update_connection_quality()
                time.sleep(1)  # Update metrics every second
            except Exception as e:
                print(f"[ERROR] Metrics simulation error: {e}")

    def simulate_weather_changes(self):
        """Simulate weather pattern changes"""
        if random.random() < 0.05:  # 5% chance of weather change every second
            self.current_weather = random.choice(list(self.weather_conditions.keys()))
            print(f"[INFO] Weather changed to: {self.current_weather}")
            
        # Apply weather effects
        weather_effect = self.weather_conditions[self.current_weather]
        self.metrics.interference_level = weather_effect['interference'] * random.uniform(0.8, 1.2)
        self.metrics.signal_strength = max(0.1, 1 - weather_effect['signal_degradation'])

    def simulate_traffic_load(self):
        """Simulate network traffic variations"""
        # Simulate daily traffic patterns
        hour = time.localtime().tm_hour
        base_load = 0.3 + 0.3 * math.sin(hour * math.pi / 12)  # Peak at noon/midnight
        variation = random.uniform(-0.1, 0.1)
        self.metrics.traffic_load = max(0, min(1, base_load + variation))

    def simulate_battery_drain(self):
        """Simulate battery usage"""
        drain_rate = 0.01 * (1 + self.metrics.traffic_load)
        self.metrics.battery_level = max(0, min(100, 
            self.metrics.battery_level - drain_rate))

    def simulate_temperature(self):
        """Simulate temperature variations based on traffic load"""
        base_temp = 20  # Base temperature in Celsius
        load_effect = self.metrics.traffic_load * 5
        self.metrics.temperature = base_temp + load_effect + random.uniform(-2, 2)

    def update_connection_quality(self):
        """Update connection quality based on various factors"""
        self.metrics.connection_quality = max(0.1, min(1.0,
            (1 - self.metrics.interference_level) *
            self.metrics.signal_strength *
            (1 - 0.5 * self.metrics.traffic_load)))

    def check_handover_loop(self):
        """Periodically check if handover is needed"""
        while self.satellite.is_running:
            try:
                self.check_handover_conditions()
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                print(f"[ERROR] Handover check error: {e}")

    def check_handover_conditions(self):
        """Check if handover is needed based on metrics and neighbor status"""
        if self.metrics.connection_quality < 0.4 or self.metrics.battery_level < 20:
            best_neighbor = self.find_best_handover_candidate()
            if best_neighbor:
                self.initiate_handover(best_neighbor)

    def find_best_handover_candidate(self) -> Optional[str]:
        """Find the best neighboring satellite for handover"""
        best_score = 0
        best_neighbor = None
        
        for neighbor_id, status in self.neighbors.items():
            if status.get('metrics'):
                score = (
                    status['metrics']['connection_quality'] * 0.4 +
                    (1 - status['metrics']['traffic_load']) * 0.3 +
                    (status['metrics']['battery_level'] / 100) * 0.3
                )
                if score > best_score:
                    best_score = score
                    best_neighbor = neighbor_id
        
        return best_neighbor

    def initiate_handover(self, target_satellite: str):
        """Initiate handover procedure to target satellite"""
        print(f"[INFO] Initiating handover to satellite {target_satellite}")
        handover_message = Message(
            sender_id=self.satellite.node_id,
            message_type=MessageType.HANDOVER,
            target_node=target_satellite,
            content={
                'ground_stations': self.satellite.ground_stations,
                'connections': list(self.satellite.connections.keys()),
                'position': vars(self.satellite.position)
            }
        )
        self.satellite._send_message(handover_message)