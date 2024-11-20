import socket
import threading
import time
import os
import base64
from message import Message, MessageType

class Node:
    def __init__(self, node_id, host, port, max_connections=5):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.connections = {}
        self.is_running = False
        self.server_socket = None
        self._lock = threading.Lock()

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_connections)
            self.is_running = True
            self.server_thread = threading.Thread(target=self.server_loop)
            self.server_thread.start()
            print(f"[INFO] Node {self.node_id} started successfully on {self.host}:{self.port}")
        except Exception as e:
            print(f"[ERROR] Failed to start node {self.node_id}: {e}")
            raise

    def stop(self):
        print(f"[INFO] Stopping node {self.node_id}...")
        self.is_running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                print(f"[ERROR] Error closing server socket: {e}")

        with self._lock:
            for node_id, conn in self.connections.items():
                try:
                    conn.close()
                    print(f"[INFO] Closed connection to node {node_id}")
                except Exception as e:
                    print(f"[ERROR] Error closing connection to {node_id}: {e}")
            self.connections.clear()

        if hasattr(self, 'server_thread'):
            try:
                self.server_thread.join(timeout=5)
                print("[INFO] Server thread stopped successfully")
            except Exception as e:
                print(f"[ERROR] Error stopping server thread: {e}")

    def server_loop(self):
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)
                try:
                    conn, addr = self.server_socket.accept()
                    conn.settimeout(60)
                    client_thread = threading.Thread(target=self.handle_connection, args=(conn, addr))
                    client_thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        print(f"[ERROR] Error accepting connection: {e}")
            except Exception as e:
                if self.is_running:
                    print(f"[ERROR] Error in server loop: {e}")
                break
        print("[INFO] Server loop ended")

    def handle_connection(self, conn, addr):
        node_id = None
        try:
            # Receive sender ID with proper handling
            sender_id_data = b""
            while b'\n' not in sender_id_data:
                chunk = conn.recv(1024)
                if not chunk:
                    return
                sender_id_data += chunk
            
            node_id = sender_id_data.split(b'\n')[0].decode().strip()
            if not node_id:
                print("[WARNING] Received empty node ID, closing connection")
                return

            with self._lock:
                self.connections[node_id] = conn
            print(f"[INFO] Connection established with {node_id} from {addr}")
            
            while self.is_running:
                try:
                    # Read message length first (fixed header size)
                    header = b""
                    remaining = 8
                    while remaining > 0:
                        chunk = conn.recv(remaining)
                        if not chunk:
                            return
                        header += chunk
                        remaining -= len(chunk)
                        
                    message_length = int.from_bytes(header, byteorder='big')
                    
                    # Read the full message
                    message_data = b""
                    while len(message_data) < message_length:
                        chunk_size = min(8192, message_length - len(message_data))
                        chunk = conn.recv(chunk_size)
                        if not chunk:
                            return
                        message_data += chunk
                    
                    # Process the message
                    message = Message.from_json(message_data.decode())
                    
                    if message.message_type == MessageType.IMAGE:
                        self._handle_image_message(message)
                    else:
                        self._handle_text_message(message)
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[ERROR] Error receiving message from {node_id}: {e}")
                    break
        finally:
            if node_id:
                with self._lock:
                    self.connections.pop(node_id, None)
            conn.close()
            print(f"[INFO] Connection closed for {node_id if node_id else 'unknown node'}")

    def _handle_text_message(self, message):
        """Handle received text message"""
        msg_type = "broadcast" if message.message_type == MessageType.BROADCAST else "direct"
        print(f"[INFO] Received {msg_type} message from {message.sender_id}")
        print(f"[INFO] Content: {message.content}")
        
        # For broadcast messages, verify this node is not the sender before displaying
        if message.message_type == MessageType.BROADCAST and message.sender_id != self.node_id:
            print(f"[INFO] Broadcast message from {message.sender_id}: {message.content}")
        # For direct messages, verify this node is the intended recipient
        elif message.message_type == MessageType.DIRECT and message.target_node == self.node_id:
            print(f"[INFO] Direct message from {message.sender_id}: {message.content}")

    def _handle_image_message(self, message):
        """Handle received image message"""
        try:
            if not message.file_info:
                print("[ERROR] Missing file information in image message")
                return
                
            # Create images directory if it doesn't exist
            os.makedirs('received_images', exist_ok=True)
            
            # Generate unique filename
            filename = f"received_images/{message.sender_id}_{int(time.time())}_{message.file_info['filename']}"
            
            # Decode and save image
            image_data = base64.b64decode(message.content)
            with open(filename, 'wb') as f:
                f.write(image_data)
                
            print(f"[INFO] Received image from {message.sender_id}, saved as {filename}")
            print(f"[INFO] Image size: {message.file_info['size']/1024:.2f}KB")
            
        except Exception as e:
            print(f"[ERROR] Failed to handle image message: {e}")