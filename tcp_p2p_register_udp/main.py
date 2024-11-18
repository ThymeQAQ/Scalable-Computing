import sys
import argparse
import signal
import time
from node import Node
from registry_client import RegistryClient, get_registry_connection

def register_node_with_server(node_id, node_ip, node_port):
    registry_host, registry_port = get_registry_connection()
    client = RegistryClient(registry_host, registry_port)
    try:
        if client.register_node(node_id, node_port):
            print(f"[INFO] Successfully registered node {node_id}")
            return client
        else:
            print(f"[ERROR] Failed to register node {node_id}")
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error during registration: {e}")
        sys.exit(1)

def get_registered_nodes():
    registry_host, registry_port = get_registry_connection()
    client = RegistryClient(registry_host, registry_port)
    try:
        return client.get_nodes()
    finally:
        client.close()

def signal_handler(signum, frame):
    print("\n[INFO] Shutting down node...")
    if hasattr(signal_handler, 'registry_client'):
        signal_handler.registry_client.close()
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
    registry_client = register_node_with_server(args.node_id, args.node_ip, args.node_port)
    signal_handler.registry_client = registry_client

    print("\n[INFO] Current registered nodes:")
    registered_nodes = get_registered_nodes()
    for nid, (ip, port) in registered_nodes.items():
        print(f"Node ID: {nid}, IP: {ip}, port: {port}")

    try:
        node = Node(args.node_id, args.node_ip, args.node_port)
        signal_handler.node = node
        node.start()

        print(f"\n[INFO] {args.node_id} is ready. Use 'send_message.py' to send messages.")
        print(f"[INFO] Connect to this node using address: {args.node_ip}:{args.node_port}")
        print("[INFO] Press Ctrl+C to stop the node")

        while True:
            time.sleep(1)

    except Exception as e:
        print(f"[ERROR] Failed to start node: {e}")
        registry_client.close()
        sys.exit(1)

if __name__ == "__main__":
    main()