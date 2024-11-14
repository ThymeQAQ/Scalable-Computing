import sys
import socket
import requests
import time
import argparse
import os
import json
from urllib.parse import urljoin
from enum import Enum, auto

class MessageType(Enum):
    DIRECT = "direct"
    BROADCAST = "broadcast"

class Message:
    def __init__(self, sender_id, message_type, content, target_node=None):
        self.sender_id = sender_id
        self.message_type = message_type
        self.content = content
        self.target_node = target_node
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    def to_json(self):
        return json.dumps({
            "sender_id": self.sender_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "target_node": self.target_node,
            "timestamp": self.timestamp
        })

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        return Message(
            data["sender_id"],
            MessageType(data["message_type"]),
            data["content"],
            data.get("target_node")
        )

def get_registry_url():
    return os.getenv('REGISTRY_URL', 'http://localhost:5000')

def get_all_nodes():
    registry_url = get_registry_url()
    try:
        response = requests.get(urljoin(registry_url, "/nodes"))
        if response.status_code == 200:
            return response.json()
        print(f"[ERROR] Failed to get nodes: {response.text}")
        return {}
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Can't connect to the registry server at {registry_url}")
        return {}
    except Exception as e:
        print(f"[ERROR] Unexpected error while getting nodes: {e}")
        return {}

def send_to_node(sender_id, target_ip, target_port, message_obj, retries=3, retry_delay=1.0):
    sock = None
    for attempt in range(retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            print(f"[DEBUG] Connecting to {target_ip}:{target_port}, attempt {attempt + 1}/{retries}")
            sock.connect((target_ip, target_port))

            # Send sender ID and message
            sock.sendall(f"{sender_id}\n".encode())
            time.sleep(0.1)
            sock.sendall(message_obj.to_json().encode())
            return True

        except ConnectionRefusedError:
            print(f"[ERROR] Connection refused by {target_ip}:{target_port}")
        except socket.timeout:
            print(f"[ERROR] Connection attempt timed out")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")

        if attempt < retries - 1:
            print(f"[INFO] Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        
        if sock:
            sock.close()

    return False

def broadcast_message(sender_id, content, exclude_nodes=None):
    if exclude_nodes is None:
        exclude_nodes = set()
    
    nodes = get_all_nodes()
    if not nodes:
        print("[ERROR] No nodes available for broadcast")
        return False

    message = Message(sender_id, MessageType.BROADCAST, content)
    success_count = 0
    total_nodes = len(nodes) - len(exclude_nodes)

    print(f"[INFO] Broadcasting message to {total_nodes} nodes...")
    
    for node_id, (ip, port) in nodes.items():
        if node_id in exclude_nodes:
            continue

        print(f"[INFO] Sending to node {node_id}...")
        if send_to_node(sender_id, ip, port, message):
            success_count += 1
            print(f"[INFO] Successfully sent to {node_id}")
        else:
            print(f"[ERROR] Failed to send to {node_id}")

    print(f"[INFO] Broadcast complete. Successfully sent to {success_count}/{total_nodes} nodes")
    return success_count > 0

def direct_message(sender_id, target_node, content):
    nodes = get_all_nodes()
    if target_node not in nodes:
        print(f"[ERROR] Target node {target_node} not found in registry")
        return False

    message = Message(sender_id, MessageType.DIRECT, content, target_node)
    target_ip, target_port = nodes[target_node]
    
    print(f"[INFO] Sending direct message to {target_node}...")
    success = send_to_node(sender_id, target_ip, target_port, message)
    
    if success:
        print(f"[INFO] Message successfully sent to {target_node}")
    else:
        print(f"[ERROR] Failed to send message to {target_node}")
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Send messages to nodes')
    parser.add_argument('sender_id', help='ID of the sending node')
    parser.add_argument('--broadcast', '-b', action='store_true', 
                      help='Broadcast message to all nodes')
    parser.add_argument('--target', '-t', help='Target node ID for direct message')
    parser.add_argument('--message', '-m', required=True, help='Message content')
    parser.add_argument('--exclude', '-e', nargs='+', help='Node IDs to exclude from broadcast')
    args = parser.parse_args()

    if args.broadcast and args.target:
        print("[ERROR] Cannot specify both broadcast and target node")
        sys.exit(1)

    if not args.broadcast and not args.target:
        print("[ERROR] Must specify either broadcast (-b) or target node (-t)")
        sys.exit(1)

    success = False
    if args.broadcast:
        exclude_nodes = set(args.exclude) if args.exclude else set()
        success = broadcast_message(args.sender_id, args.message, exclude_nodes)
    else:
        success = direct_message(args.sender_id, args.target, args.message)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()