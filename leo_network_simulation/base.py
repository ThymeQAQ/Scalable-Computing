from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
import math

if TYPE_CHECKING:
    from satellite import Satellite

@dataclass
class Position:
    """3D position representation"""
    x: float
    y: float
    z: float
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance between two positions"""
        return math.sqrt(
            (self.x - other.x) ** 2 + 
            (self.y - other.y) ** 2 + 
            (self.z - other.z) ** 2
        )

class Terminal:
    """User terminal in the LEO network"""
    def __init__(self, position: Position):
        self.position = position
        
    def find_optimal_satellite(self, satellites: List['Satellite']) -> Optional['Satellite']:
        """Find the nearest satellite to this terminal"""
        if not satellites:
            return None
        return min(satellites, key=lambda sat: self.position.distance_to(sat.position))

class GroundStation:
    """Ground station in the LEO network"""
    def __init__(self, position: Position):
        self.position = position