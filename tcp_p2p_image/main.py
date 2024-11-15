import sys
import requests
import argparse
from node import Node
import os
from urllib.parse import urljoin
import signal
import time

def get_registry_url():
    return os.getenv('REGISTRY_URL', 'http://localhost:5000')

def register_node_with_server(node_id, node_ip, node_port):
    registry_url = get_registry_url()
    try:
        response = requests.post(urljoin(registry_url, "/register"), json={
            "node_id": node_id,
            "node_ip": node_ip,
            "node_port": node_port
        })
        if response.status_code == 201:
            print(response.json()['message'])
        else:
            print(f"[ERROR] Registration failed: {response.text}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Can't connect to the registry server {registry_url}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error during registration: {e}")
        sys.exit(1)

def get_registered_nodes():
    registry_url = get_registry_url()
    try:
        response = requests.get(urljoin(registry_url, "/nodes"))
        if response.status_code == 200:
            return response.json()
        print(f"[ERROR] Failed to get nodes: {response.text}")
        return {}
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Can't connect to the registry server {registry_url}")
        return {}
    except Exception as e:
        print(f"[ERROR] Unexpected error while getting nodes: {e}")
        return {}

def signal_handler(signum, frame):
    print("\n[INFO] Shutting down node...")
    if hasattr(signal_handler, 'node'):
        signal_handler.node.stop()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Start a network node')
    parser.add_argument('node_id', help='Unique identifier for the node')
    parser.add_argument('node_ip', help='IP address for the node')
    parser.add_argument('node_port', type=int, help='Port number for the node')
    args = parser.parse_args()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"[INFO] Attempting to register node {args.node_id} with the registry server...")
    register_node_with_server(args.node_id, args.node_ip, args.node_port)

    print("\n[INFO] Current registered nodes:")
    registered_nodes = get_registered_nodes()
    for nid, (ip, port) in registered_nodes.items():
        print(f"Node ID: {nid}, IP: {ip}, port: {port}")

    try:
        node = Node(args.node_id, args.node_ip, args.node_port)
        signal_handler.node = node  # Store node reference for clean shutdown
        node.start()

        print(f"\n[INFO] {args.node_id} is ready. Use 'send_message.py' to send message.")
        print(f"[INFO] Connect to this node using address: {args.node_ip}:{args.node_port}")
        print("[INFO] Press Ctrl+C to stop the node")

        # Keep the main thread alive
        while True:
            time.sleep(1)

    except Exception as e:
        print(f"[ERROR] Failed to start node: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()