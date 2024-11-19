import sys
import socket
import time
import argparse
import os
from message import Message, MessageType
from registry_client import RegistryClient, get_registry_connection

def get_all_nodes():
    registry_host, registry_port = get_registry_connection()
    client = RegistryClient(registry_host, registry_port)
    try:
        return client.get_nodes()
    finally:
        client.close()

def send_to_node(sender_id, target_ip, target_port, message_obj, retries=3, retry_delay=1.0):
    sock = None
    for attempt in range(retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            print(f"[DEBUG] Connecting to {target_ip}:{target_port}, attempt {attempt + 1}/{retries}")
            sock.connect((target_ip, target_port))

            # Send sender ID with newline
            sender_id_bytes = f"{sender_id}\n".encode()
            print(f"[DEBUG] Sending sender ID: {sender_id}")
            sock.sendall(sender_id_bytes)
            
            # Prepare message data
            message_data = message_obj.to_json().encode()
            message_length = len(message_data)
            print(f"[DEBUG] Message length: {message_length} bytes")
            print(f"[DEBUG] Message content: {message_data.decode()}")

            # Send message length as 8-byte header
            length_header = message_length.to_bytes(8, byteorder='big')
            print(f"[DEBUG] Sending length header: {len(length_header)} bytes")
            sock.sendall(length_header)
            
            # Send message data
            total_sent = 0
            while total_sent < message_length:
                chunk_size = min(8192, message_length - total_sent)
                sent = sock.send(message_data[total_sent:total_sent + chunk_size])
                if sent == 0:
                    raise RuntimeError("Socket connection broken")
                total_sent += sent
                print(f"[DEBUG] Sent {total_sent}/{message_length} bytes")
            
            # Wait briefly to ensure data is sent
            time.sleep(0.1)
            print("[DEBUG] Message sent successfully")
            return True

        except Exception as e:
            print(f"[ERROR] Send failed: {str(e)}")
            if sock:
                sock.close()
            if attempt < retries - 1:
                print(f"[INFO] Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            return False
        finally:
            if sock:
                sock.close()

def broadcast_message(sender_id, content, exclude_nodes=None):
    if exclude_nodes is None:
        exclude_nodes = set()
    
    nodes = get_all_nodes()
    if not nodes:
        print("[ERROR] No nodes available for broadcast")
        return False

    message = Message(
        sender_id=sender_id,
        message_type=MessageType.BROADCAST,
        content=content,
        target_node=None
    )
    
    print(f"[DEBUG] Created broadcast message: {message.to_json()}")
    
    success_count = 0
    total_nodes = len(nodes) - len(exclude_nodes)

    print(f"[INFO] Broadcasting message to {total_nodes} nodes...")
    
    for node_id, (ip, port) in nodes.items():
        if node_id in exclude_nodes:
            continue

        print(f"[INFO] Sending to node {node_id} at {ip}:{port}...")
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

    message = Message(
        sender_id=sender_id,
        message_type=MessageType.DIRECT,
        content=content,
        target_node=target_node
    )
    
    print(f"[DEBUG] Created direct message: {message.to_json()}")
    
    target_ip, target_port = nodes[target_node]
    print(f"[INFO] Sending direct message to {target_node} at {target_ip}:{target_port}...")
    
    success = send_to_node(sender_id, target_ip, target_port, message)
    
    if success:
        print(f"[INFO] Message successfully sent to {target_node}")
    else:
        print(f"[ERROR] Failed to send message to {target_node}")
    
    return success

def send_image(sender_id, target_node, image_path):
    """Send an image to a specific node"""
    nodes = get_all_nodes()
    if target_node not in nodes:
        print(f"[ERROR] Target node {target_node} not found in registry")
        return False

    try:
        message = Message.create_image_message(sender_id, image_path, target_node)
        target_ip, target_port = nodes[target_node]
        
        print(f"[INFO] Sending image {image_path} to {target_node}...")
        print(f"[INFO] File size: {message.file_info['size']/1024:.2f}KB")
        
        success = send_to_node(sender_id, target_ip, target_port, message)
        
        if success:
            print(f"[INFO] Image successfully sent to {target_node}")
        else:
            print(f"[ERROR] Failed to send image to {target_node}")
        
        return success

    except Exception as e:
        print(f"[ERROR] Failed to send image: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Send messages or images to nodes')
    parser.add_argument('sender_id', help='ID of the sending node')
    parser.add_argument('--broadcast', '-b', action='store_true', 
                      help='Broadcast message to all nodes')
    parser.add_argument('--target', '-t', help='Target node ID for direct message')
    parser.add_argument('--message', '-m', help='Message content')
    parser.add_argument('--image', '-i', help='Path to image file to send')
    parser.add_argument('--exclude', '-e', nargs='+', help='Node IDs to exclude from broadcast')
    
    args = parser.parse_args()

    if args.broadcast and args.target:
        print("[ERROR] Cannot specify both broadcast and target node")
        sys.exit(1)

    if not args.broadcast and not args.target:
        print("[ERROR] Must specify either broadcast (-b) or target node (-t)")
        sys.exit(1)

    if bool(args.message) == bool(args.image):
        print("[ERROR] Must specify either message (-m) or image (-i), but not both")
        sys.exit(1)

    print(f"[DEBUG] Starting with sender_id: {args.sender_id}")
    print(f"[DEBUG] Message content: {args.message}")
    print(f"[DEBUG] Target: {args.target}")
    print(f"[DEBUG] Broadcast: {args.broadcast}")

    success = False
    if args.image:
        if args.broadcast:
            print("[ERROR] Image broadcast is not supported")
            sys.exit(1)
        success = send_image(args.sender_id, args.target, args.image)
    elif args.broadcast:
        exclude_nodes = set(args.exclude) if args.exclude else set()
        success = broadcast_message(args.sender_id, args.message, exclude_nodes)
    else:
        success = direct_message(args.sender_id, args.target, args.message)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()