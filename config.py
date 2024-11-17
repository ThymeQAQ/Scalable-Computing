from dataclasses import dataclass
from typing import Dict

@dataclass
class OrbitalConfig:
    altitude: float = 550.0  # km
    inclination: float = 53.0  # degrees
    orbital_period: float = 90.0  # minutes
    earth_radius: float = 6371.0  # km

@dataclass
class NetworkConfig:
    max_connections: int = 5
    broadcast_interval: float = 2.0  # seconds
    connection_timeout: float = 30.0  # seconds
    registry_url: str = "http://localhost:5000"

@dataclass
class SimulationConfig:
    weather_conditions: Dict[str, Dict[str, float]] = None
    battery_drain_rate: float = 0.01
    base_temperature: float = 20.0  # Celsius
    metrics_update_interval: float = 1.0  # seconds
    handover_check_interval: float = 5.0  # seconds
    
    def __post_init__(self):
        if self.weather_conditions is None:
            self.weather_conditions = {
                'clear': {'interference': 0.1, 'signal_degradation': 0.1},
                'cloudy': {'interference': 0.3, 'signal_degradation': 0.3},
                'storm': {'interference': 0.7, 'signal_degradation': 0.6}
            }