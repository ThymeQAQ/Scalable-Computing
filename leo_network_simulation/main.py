import argparse
import time
import sys
import math
from typing import Optional
from base import Position, Terminal, GroundStation
from satellite import Satellite
from leo_network import LEONetwork

class ScenarioSimulator:
    """Class to simulate different LEO network scenarios"""
    
    @staticmethod
    def create_polar_orbit_network():
        """Create a network with satellites in polar orbit"""
        satellites = [
            Satellite(
                position=Position(0, 0, 1000),
                coverage_radius=800,
                orbital_period=90 * 60,
                orbital_radius=1000,
                initial_angle=i * (2 * math.pi / 6),
                orbit_type='polar',
                inclination=math.pi/2
            )
            for i in range(6)
        ]
        
        ground_stations = [
            GroundStation(Position(0, 2000, 0)),
            GroundStation(Position(0, -2000, 0)),
            GroundStation(Position(1500, 0, 0)),
        ]
        
        return LEONetwork(satellites, ground_stations)

    @staticmethod
    def create_dense_coverage_network():
        """Create a network with dense satellite coverage"""
        satellites = []
        for i in range(5):  # 5 satellites in orbital plane
            for j in range(3):  # 3 orbital planes
                angle = i * (2 * math.pi / 5)  # Fixed: Changed from 12 to 5
                inclination = j * (math.pi / 6)  # Dip intervals between orbital planes
                satellites.append(
                    Satellite(
                        position=Position(
                            1000 * math.cos(angle) * math.cos(inclination),
                            1000 * math.sin(angle),
                            1000 * math.sin(inclination)
                        ),
                        coverage_radius=600,
                        orbital_period=95 * 60,
                        orbital_radius=1000,
                        initial_angle=angle,
                        orbit_type='polar',
                        inclination=inclination
                    )
                )
        
        def create_uniform_ground_stations(num_stations: int, radius: float = 1500) -> list:
            """
            Create uniformly distributed ground stations around a circle
            Args:
                num_stations: Number of ground stations to create
                radius: Distance from center point (in kilometers)
            Returns:
                List of ground stations
            """
            return [
                GroundStation(Position(
                    radius * math.cos(i * 2 * math.pi / num_stations),  # x coordinate
                    radius * math.sin(i * 2 * math.pi / num_stations),  # y coordinate
                    0  # z coordinate (always 0 for ground stations)
                ))
                for i in range(num_stations)
            ]

        # Create ground stations with specified configuration
        ground_stations = create_uniform_ground_stations(
            num_stations=4,  # Set desired number of ground stations
            radius=1500      # Set radius from center point
        )
        
        return LEONetwork(satellites, ground_stations)

    @staticmethod
    def create_emergency_scenario_network():
        """Create a network simulating emergency conditions"""
        satellites = []
        num_sats_per_plane = 3  # Number of satellites per orbital plane
        num_planes = 1          # Number of orbital planes
        
        for i in range(num_sats_per_plane):
            for j in range(num_planes):
                angle = i * (2 * math.pi / num_sats_per_plane)
                inclination = j * (math.pi / 3)  # 60 degrees interval between orbital planes
                satellites.append(
                    Satellite(
                        position=Position(
                            1000 * math.cos(angle) * math.cos(inclination),
                            1000 * math.sin(angle),
                            1000 * math.cos(angle) * math.sin(inclination)
                        ),
                        coverage_radius=900,
                        orbital_period=100 * 60,
                        orbital_radius=1000,
                        initial_angle=angle,
                        orbit_type='polar',      # Use polar orbit for better coverage
                        inclination=inclination
                    )
                )
        
        def create_uniform_ground_stations(num_stations: int = 2, radius: float = 1200):
            """
            Create uniformly distributed ground stations around a circle
            Args:
                num_stations: Number of ground stations to create
                radius: Distance from center point (in kilometers)
            Returns:
                List of ground stations
            """
            return [
                GroundStation(Position(
                    radius * math.cos(i * 2 * math.pi / num_stations),  # x coordinate
                    radius * math.sin(i * 2 * math.pi / num_stations),  # y coordinate
                    0  # z coordinate (always 0 for ground stations)
                ))
                for i in range(num_stations)
            ]
        
        # Create ground stations with specified configuration
        ground_stations = create_uniform_ground_stations(
            num_stations=3,  # Set number of ground stations
            radius=1200      # Set radius from center point
        )
        
        return LEONetwork(satellites, ground_stations)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='LEO Network Simulation System',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '--scenario',
        type=str,
        choices=['polar', 'dense', 'emergency', 'all'],
        default='all',
        help='Scenario type to simulate:\n'
             'polar: Polar orbit configuration\n'
             'dense: Dense coverage configuration\n'
             'emergency: Emergency scenario\n'
             'all: Run all scenarios'
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=180,
        help='Simulation duration in seconds (default: 180)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=30,
        help='Time interval between checks in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--visualize',
        action='store_true',
        default=False,
        help='Enable 3D visualization (default: False)'
    )
    
    parser.add_argument(
        '--terminal-position',
        type=float,
        nargs=3,
        metavar=('X', 'Y', 'Z'),
        default=None,
        help='Custom terminal position (x y z) in km'
    )

    # Add new arguments for relay parameters
    parser.add_argument(
        '--max-relay-hops',
        type=int,
        default=3,
        help='Maximum number of relay hops allowed (default: 3)'
    )
    
    parser.add_argument(
        '--max-retry-attempts',
        type=int,
        default=3,
        help='Maximum number of retry attempts (default: 3)'
    )
    
    parser.add_argument(
        '--retry-delay',
        type=float,
        default=10,
        help='Delay between retry attempts in seconds (default: 10)'
    )

    return parser.parse_args()

def run_scenario_simulation(
    scenario_type: str,
    duration: float = 300,
    interval: float = 30,
    visualize: bool = True,
    terminal: Terminal = None,
    max_relay_hops: int = 3,      
    max_retry_attempts: int = 3,   
    retry_delay: float = 10       
):
    """
    Run simulation for a specific scenario with enhanced relay capabilities
    
    Args:
        scenario_type: Type of scenario to simulate
        duration: Total simulation duration in seconds
        interval: Time interval between checks in seconds
        visualize: Enable 3D visualization
        terminal: Custom terminal position (optional)
        max_relay_hops: Maximum allowed relay hops
        max_retry_attempts: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    """
    # Create network based on scenario
    if scenario_type == 'polar':
        network = ScenarioSimulator.create_polar_orbit_network()
        default_terminal = Terminal(Position(0, 1500, 0))
    elif scenario_type == 'dense':
        network = ScenarioSimulator.create_dense_coverage_network()
        default_terminal = Terminal(Position(500, 500, 0))
    elif scenario_type == 'emergency':
        network = ScenarioSimulator.create_emergency_scenario_network()
        default_terminal = Terminal(Position(0, 0, 0))
    else:
        raise ValueError("Invalid scenario type")

    # Set improved relay parameters
    network.max_relay_hops = max_relay_hops
    network.max_retry_attempts = max_retry_attempts
    network.retry_delay = retry_delay

    # Use custom terminal if provided, otherwise use default
    terminal = terminal or default_terminal

    print(f"\nRunning {scenario_type} scenario simulation...")
    print(f"Network configuration:")
    print(f"- Number of satellites: {len(network.satellites)}")
    print(f"- Number of ground stations: {len(network.ground_stations)}")
    print(f"- Terminal position: ({terminal.position.x}, {terminal.position.y}, {terminal.position.z})")
    print(f"- Duration: {duration} seconds")
    print(f"- Check interval: {interval} seconds")
    print(f"- Maximum relay hops: {max_relay_hops}")
    print(f"- Maximum retry attempts: {max_retry_attempts}")
    print(f"- Retry delay: {retry_delay} seconds")
    
    if visualize:
        network.visualize_network(terminal)
    
    start_time = time.time()
    sim_time = 0
    successful_transmissions = 0
    total_attempts = 0
    
    while sim_time < duration:
        current_time = start_time + sim_time
        print(f"\nTime: {sim_time:.1f} seconds")
        
        success, path = network.simulate_transmission(terminal, "Test Data", current_time)
        
        total_attempts += 1
        if success:
            successful_transmissions += 1
        
        print("Transmission Status:", "Success" if success else "Failed")
        print("Path:")
        for step in path:
            print(f"- {step}")
        
        if visualize and sim_time % 60 == 0:
            network.visualize_network(terminal)
            
        sim_time += interval
        time.sleep(1)
    
    print("\nSimulation Complete")
    print(f"Success Rate: {(successful_transmissions/total_attempts)*100:.1f}%")
    print(f"Total Transmissions: {total_attempts}")
    print(f"Successful Transmissions: {successful_transmissions}")

def main():
    """Main function to run the simulation"""
    args = parse_arguments()
    
    if args.terminal_position:
        custom_terminal = Terminal(
            Position(
                args.terminal_position[0],
                args.terminal_position[1],
                args.terminal_position[2]
            )
        )
    else:
        custom_terminal = None

    scenarios = ['polar', 'dense', 'emergency'] if args.scenario == 'all' else [args.scenario]
    
    for scenario in scenarios:
        try:
            print(f"\nStarting {scenario} scenario simulation...")
            run_scenario_simulation(
                scenario_type=scenario,
                duration=args.duration,
                interval=args.interval,
                visualize=args.visualize,
                terminal=custom_terminal,
                max_relay_hops=args.max_relay_hops,
                max_retry_attempts=args.max_retry_attempts,
                retry_delay=args.retry_delay
            )
        except Exception as e:
            print(f"Error in {scenario} scenario: {str(e)}")
            continue

if __name__ == "__main__":
    main()