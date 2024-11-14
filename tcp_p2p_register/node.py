import socket
import threading
import time

class Node:
    def __init__(self, node_id, host, port, max_connections=5):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self.connections = {}
        self.is_running = False
        self.server_socket = None
        self._lock = threading.Lock()  # Add lock for thread safety

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_connections)
            self.is_running = True
            self.server_thread = threading.Thread(target=self.server_loop)
            self.server_thread.start()  # Remove daemon=True to prevent premature exit
            print(f"[INFO] Node {self.node_id} started successfully on {self.host}:{self.port}")
        except Exception as e:
            print(f"[ERROR] Failed to start node {self.node_id}: {e}")
            raise

    def stop(self):
        print(f"[INFO] Stopping node {self.node_id}...")
        self.is_running = False
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                print(f"[ERROR] Error closing server socket: {e}")

        # Close all client connections
        with self._lock:
            for node_id, conn in self.connections.items():
                try:
                    conn.close()
                    print(f"[INFO] Closed connection to node {node_id}")
                except Exception as e:
                    print(f"[ERROR] Error closing connection to {node_id}: {e}")
            self.connections.clear()

        # Wait for server thread to complete
        if hasattr(self, 'server_thread'):
            try:
                self.server_thread.join(timeout=5)  # Wait up to 5 seconds
                print("[INFO] Server thread stopped successfully")
            except Exception as e:
                print(f"[ERROR] Error stopping server thread: {e}")

    def server_loop(self):
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)  # Add timeout to allow checking is_running
                try:
                    conn, addr = self.server_socket.accept()
                    conn.settimeout(60)  # Set timeout for connections
                    client_thread = threading.Thread(target=self.handle_connection, args=(conn, addr))
                    client_thread.start()
                except socket.timeout:
                    continue  # Check is_running condition
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
            node_id = conn.recv(1024).decode().strip()
            if not node_id:
                print("[WARNING] Received empty node ID, closing connection")
                return

            with self._lock:
                self.connections[node_id] = conn
            print(f"[INFO] Connection established with {node_id} from {addr}")
            
            while self.is_running:
                try:
                    message = conn.recv(1024).decode()
                    if not message:
                        break
                    print(f"[INFO] Message from {node_id}: {message}")
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[ERROR] Error receiving message from {node_id}: {e}")
                    break
        except Exception as e:
            print(f"[ERROR] Error handling connection: {e}")
        finally:
            if node_id:
                with self._lock:
                    self.connections.pop(node_id, None)
            conn.close()
            print(f"[INFO] Connection closed for {node_id if node_id else 'unknown node'}")