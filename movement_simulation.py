
import numpy as np
import time
from typing import Tuple, List

def init_satellites(orbit_z_axis: Tuple[float, float], num_sats: int) -> List[Tuple[float, float]]:
    """Initialize satellites in a circular orbit pattern."""
    sat_ll_list = []
    orbit_radius = 45  # degrees from center
    
    for i in range(num_sats):
        angle = (2 * np.pi * i) / num_sats
        lat = orbit_z_axis[0] + orbit_radius * np.cos(angle)
        lon = orbit_z_axis[1] + orbit_radius * np.sin(angle)
        sat_ll_list.append((lat, lon))
    
    return sat_ll_list

def satellites_move(current_pos: Tuple[float, float], orbit_z_axis: Tuple[float, float], 
                   velocity: float, time_delta: float) -> Tuple[float, float]:
    """Calculate new satellite position based on orbital movement."""
    current_lat, current_lon = current_pos
    center_lat, center_lon = orbit_z_axis
    
    # Calculate current angle in the orbit
    angle = np.arctan2(current_lon - center_lon, current_lat - center_lat)
    
    # Update angle based on velocity and time
    new_angle = angle + velocity * time_delta
    
    # Calculate new position
    orbit_radius = np.sqrt((current_lat - center_lat)**2 + (current_lon - center_lon)**2)
    new_lat = center_lat + orbit_radius * np.cos(new_angle)
    new_lon = center_lon + orbit_radius * np.sin(new_angle)
    
    return new_lat, new_lon