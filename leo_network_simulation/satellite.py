import math
import time
from typing import List, Optional
from base import Position, GroundStation

class Satellite:
    """Satellite in the LEO network with orbital movement"""
    def __init__(
        self,
        position: Position,
        coverage_radius: float,
        orbital_period: float,
        orbital_radius: float,
        initial_angle: float = 0,
        orbit_type: str = 'circular',
        inclination: float = 0
    ):
        self.position = position
        self.coverage_radius = coverage_radius
        self.orbital_period = orbital_period
        self.orbital_radius = orbital_radius
        self.initial_angle = initial_angle
        self.orbit_type = orbit_type
        self.inclination = inclination
        self.start_time = time.time()
        
        # Network status attributes
        self.visible_satellites: List['Satellite'] = []
        self.visible_ground_stations: List[GroundStation] = []
        
    def update_position(self, current_time: float = None) -> None:
        """Update satellite position based on orbital parameters"""
        if current_time is None:
            current_time = time.time()
            
        elapsed_time = current_time - self.start_time
        angle = self.initial_angle + (2 * math.pi * elapsed_time / self.orbital_period)
        
        if self.orbit_type == 'circular':
            self.position.x = self.orbital_radius * math.cos(angle)
            self.position.y = self.orbital_radius * math.sin(angle)
            self.position.z = self.position.z  # Maintain current z-position
        elif self.orbit_type == 'polar':
            self.position.x = self.orbital_radius * math.cos(angle) * math.cos(self.inclination)
            self.position.y = self.orbital_radius * math.sin(angle)
            self.position.z = self.orbital_radius * math.cos(angle) * math.sin(self.inclination)
            
    def is_in_coverage(self, position: Position) -> bool:
        """Check if a position is within satellite's coverage"""
        return self.position.distance_to(position) <= self.coverage_radius
        
    def find_optimal_ground_station(self, ground_stations: List[GroundStation]) -> Optional[GroundStation]:
        """Find nearest ground station within coverage"""
        available_stations = [
            station for station in ground_stations 
            if self.is_in_coverage(station.position)
        ]
        
        if not available_stations:
            return None
            
        return min(
            available_stations,
            key=lambda station: self.position.distance_to(station.position)
        )
        
    def find_nearest_satellite(self, satellites: List['Satellite']) -> Optional['Satellite']:
        """Find nearest satellite for relay"""
        other_satellites = [sat for sat in satellites if sat is not self]
        if not other_satellites:
            return None
            
        return min(
            other_satellites,
            key=lambda sat: self.position.distance_to(sat.position)
        )