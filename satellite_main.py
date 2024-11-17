import sys
import requests
import argparse
from satellite import LEOSatelliteNode, Position, SatelliteStatus
from simulation import SatelliteMonitor, SatelliteMetrics
from config import OrbitalConfig, NetworkConfig, SimulationConfig
import os
from urllib.parse import urljoin
import signal
import time
import math
import random
import threading
from typing import Optional, Dict
import json

class SatelliteController:
    def __init__(self, satellite: LEOSatelliteNode, monitor: SatelliteMonitor):
        self.satellite = satellite
        self.monitor = monitor
        self.is_running = True
        self._lock = threading.Lock()
        self.handover_in_progress = False
        
    def start_monitoring(self):
        """Start monitoring threads"""
        self.status_thread = threading.Thread(target=self._status_display_loop)
        self.status_thread.daemon = True
        self.status_thread.start()
        
    def _status_display_loop(self):
        """Display satellite status and metrics periodically"""
        while self.is_running:
            self._display_status()
            time.sleep(5)
            
    def _display_status(self):
        """Display current satellite status and metrics"""
        metrics = self.monitor.metrics
        position = self.satellite.position
        
        print("\n" + "="*50)
        print(f"Satellite Status Report - {self.satellite.node_id}")
        print("="*50)
        
        # Position Information
        print("\nPosition:")
        print(f"  Latitude:  {position.latitude:.2f}°")
        print(f"  Longitude: {position.longitude:.2f}°")
        print(f"  Altitude:  {position.altitude:.2f} km")
        
        # Connection Status
        print("\nConnection Status:")
        print(f"  Active Connections: {len(self.satellite.connections)}")
        print(f"  Satellite Status:   {self.satellite.status.value}")
        
        # Metrics
        print("\nMetrics:")
        print(f"  Connection Quality: {metrics.connection_quality:.2f}")
        print(f"  Traffic Load:       {metrics.traffic_load:.2f}")
        print(f"  Signal Strength:    {metrics.signal_strength:.2f}")
        print(f"  Battery Level:      {metrics.battery_level:.1f}%")
        
        # Handover Status
        if self.handover_in_progress:
            print("\nHandover in progress...")
            
        print("\nNeighboring Satellites:")
        for neighbor_id, data in self.monitor.neighbors.items():
            if data.get('metrics'):
                print(f"  {neighbor_id}: Quality={data['metrics']['connection_quality']:.2f}, "
                      f"Battery={data['metrics']['battery_level']:.1f}%")
        
    def stop(self):
        """Stop the controller and satellite"""
        self.is_running = False
        self.satellite.stop()

def generate_orbital_position(satellite_index: int, total_satellites: int) -> Position:
    """Generate initial orbital position for a satellite in a constellation"""
    angle = (360.0 / total_satellites) * satellite_index
    rad = math.radians(angle)
    
    altitude = 550  # km
    earth_radius = 6371  # km
    
    latitude = 53.0 * math.cos(rad)  # 53° orbital inclination
    longitude = angle
    
    return Position(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        timestamp=time.time()
    )

def register_with_registry(registry_url: str, data: dict) -> bool:
    """Register satellite with the registry server"""
    try:
        response = requests.post(urljoin(registry_url, "/register"), json=data)
        if response.status_code == 201:
            print(f"[SUCCESS] Satellite registered successfully")
            return True
        print(f"[ERROR] Registration failed: {response.text}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to registry server at {registry_url}")
        return False
    except Exception as e:
        print(f"[ERROR] Registration error: {e}")
        return False

def handle_handover_request(controller: SatelliteController, target_id: str):
    """Handle handover request to target satellite"""
    print(f"\n[HANDOVER] Initiating handover to satellite {target_id}")
    controller.handover_in_progress = True
    
    # Your handover logic here
    # For example:
    # 1. Pause new connections
    # 2. Transfer existing connections
    # 3. Update satellite status
    
    controller.satellite.status = SatelliteStatus.HANDOVER
    time.sleep(2)  # Simulate handover process
    controller.handover_in_progress = False
    controller.satellite.status = SatelliteStatus.ACTIVE
    print(f"[HANDOVER] Handover to {target_id} completed")

def main():
    parser = argparse.ArgumentParser(description='Start a LEO satellite node with monitoring')
    parser.add_argument('node_id', help='Unique identifier for the satellite')
    parser.add_argument('node_ip', help='IP address for the satellite node')
    parser.add_argument('node_port', type=int, help='Port number for the satellite node')
    parser.add_argument('--orbital-period', type=float, default=90, 
                       help='Orbital period in minutes (default: 90)')
    parser.add_argument('--constellation-size', type=int, default=5,
                       help='Total number of satellites in constellation (default: 5)')
    parser.add_argument('--satellite-index', type=int, required=True,
                       help='Index of this satellite in the constellation (0 to constellation_size-1)')
    parser.add_argument('--registry-url', default='http://localhost:5000',
                       help='URL of the registry server')
    
    args = parser.parse_args()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print("\n[INFO] Shutting down satellite node...")
        if hasattr(signal_handler, 'controller'):
            signal_handler.controller.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Generate initial position
    initial_position = generate_orbital_position(
        args.satellite_index, 
        args.constellation_size
    )
    
    print(f"\n[INIT] Initializing satellite {args.node_id}")
    print(f"Position: lat={initial_position.latitude:.2f}°, "
          f"lon={initial_position.longitude:.2f}°, "
          f"alt={initial_position.altitude}km")
    
    # Register with registry server
    registration_data = {
        "node_id": args.node_id,
        "node_ip": args.node_ip,
        "node_port": args.node_port,
        "satellite_data": {
            "latitude": initial_position.latitude,
            "longitude": initial_position.longitude,
            "altitude": initial_position.altitude
        }
    }
    
    if not register_with_registry(args.registry_url, registration_data):
        sys.exit(1)
    
    try:
        # Initialize satellite
        satellite = LEOSatelliteNode(
            node_id=args.node_id,
            host=args.node_ip,
            port=args.node_port,
            initial_position=initial_position,
            orbital_period=args.orbital_period
        )
        
        # Initialize monitor and controller
        monitor = SatelliteMonitor(satellite)
        controller = SatelliteController(satellite, monitor)
        signal_handler.controller = controller
        
        # Start satellite and monitoring
        satellite.start()
        controller.start_monitoring()
        
        print(f"\n[INFO] Satellite {args.node_id} is operational")
        print(f"[INFO] Orbital period: {args.orbital_period} minutes")
        print(f"[INFO] Status: {satellite.status.value}")
        print("[INFO] Press Ctrl+C to terminate the satellite")
        
        # Main loop
        while True:
            # Check for handover conditions
            if monitor.metrics.connection_quality < 0.4 or monitor.metrics.battery_level < 20:
                best_neighbor = monitor.find_best_handover_candidate()
                if best_neighbor and not controller.handover_in_progress:
                    handle_handover_request(controller, best_neighbor)
            
            time.sleep(1)
            
    except Exception as e:
        print(f"[ERROR] Satellite operation error: {e}")
        if hasattr(signal_handler, 'controller'):
            signal_handler.controller.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()