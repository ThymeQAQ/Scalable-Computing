import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from typing import List, Tuple, Set, Optional
import time

from base import Position, Terminal, GroundStation
from satellite import Satellite


class LEONetwork:
    """Management class for the entire LEO network"""
    def __init__(
        self,
        satellites: List[Satellite],
        ground_stations: List[GroundStation],
        max_relay_hops: int = 3,
        max_retry_attempts: int = 3,
        retry_delay: float = 10
    ):
        self.satellites = satellites
        self.ground_stations = ground_stations
        self.transmission_history = []
        self.max_relay_hops = max_relay_hops
        self.max_retry_attempts = max_retry_attempts
        self.retry_delay = retry_delay
        self.current_time = 0

    def update_network(self, current_time: float = None) -> None:
        """Update positions of all satellites and network status"""
        if current_time is not None:
            self.current_time = current_time
            
        for satellite in self.satellites:
            satellite.update_position(current_time)
            
        self._update_network_status()

    def _update_network_status(self) -> None:
        """Update network status including visibility and connections"""
        for sat in self.satellites:
            sat.visible_satellites = []
            for other_sat in self.satellites:
                if sat != other_sat and sat.is_in_coverage(other_sat.position):
                    sat.visible_satellites.append(other_sat)
        
        for sat in self.satellites:
            sat.visible_ground_stations = []
            for gs in self.ground_stations:
                if sat.is_in_coverage(gs.position):
                    sat.visible_ground_stations.append(gs)

    def find_path_to_ground_station(
        self, 
        start_satellite: Satellite, 
        visited_satellites: Set[Satellite] = None,
        current_hop: int = 0
    ) -> Tuple[bool, List[Satellite], Optional[GroundStation]]:
        """Find path from satellite to ground station"""
        if visited_satellites is None:
            visited_satellites = set()
            
        if current_hop >= self.max_relay_hops:
            return False, [], None
            
        visited_satellites.add(start_satellite)
        
        ground_station = start_satellite.find_optimal_ground_station(self.ground_stations)
        if ground_station:
            return True, [start_satellite], ground_station
            
        satellites_by_distance = sorted(
            [sat for sat in self.satellites if sat not in visited_satellites],
            key=lambda sat: start_satellite.position.distance_to(sat.position)
        )
        
        for next_satellite in satellites_by_distance:
            success, path, station = self.find_path_to_ground_station(
                next_satellite,
                visited_satellites.copy(),
                current_hop + 1
            )
            if success:
                return True, [start_satellite] + path, station
                
        return False, [], None

    def simulate_transmission(
        self, 
        terminal: Terminal, 
        data: str,
        current_time: float = None
    ) -> Tuple[bool, List[str]]:
        """Simulate data transmission with retry mechanism"""
        path = []
        retry_count = 0
        
        while retry_count < self.max_retry_attempts:
            self.update_network(current_time)
            
            optimal_satellite = terminal.find_optimal_satellite(self.satellites)
            if not optimal_satellite:
                return False, ["No available satellite found"]
                
            path = [f"Terminal -> Satellite at ({optimal_satellite.position.x:.1f}, "
                   f"{optimal_satellite.position.y:.1f}, {optimal_satellite.position.z:.1f})"]
            
            success, satellite_path, final_station = self.find_path_to_ground_station(optimal_satellite)
            
            if success:
                for i in range(len(satellite_path) - 1):
                    path.append(
                        f"Satellite -> Relay Satellite ({satellite_path[i+1].position.x:.1f}, "
                        f"{satellite_path[i+1].position.y:.1f}, {satellite_path[i+1].position.z:.1f})"
                    )
                    
                path.append(
                    f"Satellite -> Ground Station ({final_station.position.x:.1f}, "
                    f"{final_station.position.y:.1f}, {final_station.position.z:.1f})"
                )
                return True, path
                
            retry_count += 1
            if retry_count < self.max_retry_attempts:
                path.append(f"No path found, retrying in {self.retry_delay} seconds... "
                          f"(Attempt {retry_count + 1}/{self.max_retry_attempts})")
                if current_time is not None:
                    current_time += self.retry_delay
            else:
                path.append("Maximum retry attempts reached, transmission failed")
                
        return False, path

    def visualize_network(self, terminal: Optional[Terminal] = None) -> None:
        """Visualize current network state in 3D"""
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot satellites
        sat_positions = [(s.position.x, s.position.y, s.position.z) for s in self.satellites]
        if sat_positions:
            xs, ys, zs = zip(*sat_positions)
            ax.scatter(xs, ys, zs, c='blue', marker='^', s=100, label='Satellites')
        
        # Plot ground stations
        gs_positions = [(gs.position.x, gs.position.y, gs.position.z) for gs in self.ground_stations]
        if gs_positions:
            xs, ys, zs = zip(*gs_positions)
            ax.scatter(xs, ys, zs, c='green', marker='s', s=100, label='Ground Stations')
        
        if terminal:
            ax.scatter([terminal.position.x], [terminal.position.y], [terminal.position.z],
                      c='red', marker='o', s=100, label='Terminal')
        
        ax.set_xlabel('X (km)')
        ax.set_ylabel('Y (km)')
        ax.set_zlabel('Z (km)')
        ax.grid(True)
        ax.legend()
        
        plt.title('LEO Network Visualization')
        if self.current_time:
            plt.suptitle(f'Time: {self.current_time:.1f} seconds', y=0.95)
        
        plt.show()