from dataclasses import dataclass
import time
import math

@dataclass
class GroundStation:
    station_id: str
    latitude: float
    longitude: float
    status: str = "active"
    last_contact: float = None
    
    def update_contact(self):
        self.last_contact = time.time()

class GroundStationManager:
    def __init__(self):
        self.stations = {}
        
    def add_station(self, station: GroundStation):
        self.stations[station.station_id] = station
        
    def remove_station(self, station_id: str):
        self.stations.pop(station_id, None)
        
    def get_visible_stations(self, sat_lat: float, sat_lon: float, max_distance: float = 1000) -> list:
        """Returns list of ground stations visible to satellite"""
        visible = []
        for station in self.stations.values():  # Changed from list indexing to dict values
            if self._is_visible(sat_lat, sat_lon, station.latitude, station.longitude, max_distance):
                visible.append(station)
        return visible
    
    def _is_visible(self, sat_lat: float, sat_lon: float, 
                    station_lat: float, station_lon: float, max_distance: float) -> bool:
        """
        Simple visibility check based on great circle distance.
        Uses Haversine formula for better accuracy.
        """
        # Convert latitude and longitude to radians
        sat_lat_rad = math.radians(sat_lat)
        sat_lon_rad = math.radians(sat_lon)
        station_lat_rad = math.radians(station_lat)
        station_lon_rad = math.radians(station_lon)
        
        # Calculate differences
        dlat = station_lat_rad - sat_lat_rad
        dlon = station_lon_rad - sat_lon_rad
        
        # Haversine formula
        a = math.sin(dlat/2)**2 + math.cos(sat_lat_rad) * math.cos(station_lat_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        R = 6371.0
        
        # Calculate distance
        distance = R * c
        
        return distance <= max_distance

# Example usage:
if __name__ == "__main__":
    # Create a ground station manager
    manager = GroundStationManager()
    
    # Add some example ground stations
    station1 = GroundStation("GS1", latitude=40.7128, longitude=-74.0060)  # New York
    station2 = GroundStation("GS2", latitude=51.5074, longitude=-0.1278)   # London
    station3 = GroundStation("GS3", latitude=35.6762, longitude=139.6503)  # Tokyo
    
    manager.add_station(station1)
    manager.add_station(station2)
    manager.add_station(station3)
    
    # Test visibility from a satellite position
    test_lat = 42.0
    test_lon = -71.0
    visible_stations = manager.get_visible_stations(test_lat, test_lon)
    
    print(f"Visible stations from {test_lat}, {test_lon}:")
    for station in visible_stations:
        print(f"- {station.station_id} at ({station.latitude}, {station.longitude})")