import socket
import json
import threading
import time
from typing import Dict, Tuple

class UDPRegistry:
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.host = host
        self.port = port
        self.nodes: Dict[str, Tuple[str, int]] = {}
        self.lock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.is_running = False
        self.last_heartbeat = {}  # Store last heartbeat time for each node
        print(f"[DEBUG] Registry initialized with host={host}, port={port}")

    def start(self):
        try:
            self.socket.bind((self.host, self.port))
            self.is_running = True
            print(f"[INFO] UDP Registry server started on {self.host}:{self.port}")
            print("[DEBUG] Server socket bound successfully")
            self._start_heartbeat_checker()
            self._handle_requests()
        except Exception as e:
            print(f"[ERROR] Failed to start UDP registry server: {e}")
            self.stop()

    def stop(self):
        print("[DEBUG] Stopping registry server...")
        self.is_running = False
        if hasattr(self, 'socket'):
            try:
                self.socket.close()
                print("[DEBUG] Server socket closed")
            except Exception as e:
                print(f"[ERROR] Error closing socket: {e}")
        print("[INFO] Registry server stopped")

    def _start_heartbeat_checker(self):
        def check_heartbeats():
            print("[DEBUG] Starting heartbeat checker thread")
            while self.is_running:
                time.sleep(30)  # Check every 30 seconds
                current_time = time.time()
                with self.lock:
                    # Remove nodes that haven't sent a heartbeat in 90 seconds
                    inactive_nodes = [
                        node_id for node_id, last_time in self.last_heartbeat.items()
                        if current_time - last_time > 90
                    ]
                    for node_id in inactive_nodes:
                        print(f"[INFO] Removing inactive node: {node_id}")
                        print(f"[DEBUG] Last heartbeat was {current_time - self.last_heartbeat[node_id]:.2f} seconds ago")
                        self.nodes.pop(node_id, None)
                        self.last_heartbeat.pop(node_id, None)
                    if inactive_nodes:
                        print(f"[DEBUG] Current active nodes after cleanup: {self.nodes}")
        
        thread = threading.Thread(target=check_heartbeats)
        thread.daemon = True
        thread.start()
        print("[DEBUG] Heartbeat checker thread started")

    def _handle_requests(self):
        print("[DEBUG] Starting request handler")
        while self.is_running:
            try:
                print("\n[DEBUG] Waiting for incoming requests...")
                data, client_addr = self.socket.recvfrom(4096)
                print(f"[DEBUG] Received {len(data)} bytes from {client_addr}")
                try:
                    request = json.loads(data.decode())
                    print(f"[DEBUG] Parsed request from {client_addr}: {request}")
                    self._process_request(request, client_addr)
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Invalid JSON received from {client_addr}: {e}")
                    print(f"[DEBUG] Raw data received: {data}")
            except Exception as e:
                if self.is_running:
                    print(f"[ERROR] Error handling request: {e}")

    def _process_request(self, request: dict, addr: Tuple[str, int]):
        command = request.get('command')
        print(f"[DEBUG] Processing {command} command from {addr}")
        
        if command == 'register':
            self._handle_register(request, addr)
        elif command == 'get_nodes':
            self._handle_get_nodes(addr)
        elif command == 'heartbeat':
            self._handle_heartbeat(request, addr)
        elif command == 'unregister':
            self._handle_unregister(request, addr)
        else:
            print(f"[WARNING] Unknown command received: {command}")
            self._send_response({
                'status': 'error',
                'message': f'Unknown command: {command}'
            }, addr)

    def _handle_register(self, request: dict, addr: Tuple[str, int]):
        node_id = request.get('node_id')
        node_port = request.get('node_port')
        print(f"[DEBUG] Processing registration request:")
        print(f"[DEBUG] Node ID: {node_id}")
        print(f"[DEBUG] Client Address: {addr}")
        print(f"[DEBUG] Node Port: {node_port}")

        if not all([node_id, node_port]):
            print(f"[ERROR] Missing required fields in registration request")
            self._send_response({
                'status': 'error',
                'message': 'Missing required fields'
            }, addr)
            return

        with self.lock:
            self.nodes[node_id] = (addr[0], node_port)
            self.last_heartbeat[node_id] = time.time()
            print(f"[INFO] Registered node {node_id} at {addr[0]}:{node_port}")
            print(f"[DEBUG] Current registered nodes: {self.nodes}")
            self._send_response({
                'status': 'success',
                'message': f'Node {node_id} registered successfully'
            }, addr)

    def _handle_unregister(self, request: dict, addr: Tuple[str, int]):
        node_id = request.get('node_id')
        print(f"[DEBUG] Processing unregister request for node {node_id} from {addr}")

        if not node_id:
            print(f"[ERROR] Missing node_id in unregister request")
            self._send_response({
                'status': 'error',
                'message': 'Missing node_id'
            }, addr)
            return

        with self.lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                self.last_heartbeat.pop(node_id, None)
                print(f"[INFO] Unregistered node {node_id}")
                print(f"[DEBUG] Current registered nodes: {self.nodes}")
                self._send_response({
                    'status': 'success',
                    'message': f'Node {node_id} unregistered successfully'
                }, addr)
            else:
                print(f"[WARNING] Attempt to unregister unknown node {node_id}")
                self._send_response({
                    'status': 'error',
                    'message': f'Node {node_id} not found'
                }, addr)

    def _handle_get_nodes(self, addr: Tuple[str, int]):
        print(f"[DEBUG] Processing get_nodes request from {addr}")
        with self.lock:
            print(f"[DEBUG] Returning node list: {self.nodes}")
            self._send_response({
                'status': 'success',
                'nodes': self.nodes
            }, addr)

    def _handle_heartbeat(self, request: dict, addr: Tuple[str, int]):
        node_id = request.get('node_id')
        print(f"[DEBUG] Processing heartbeat from node {node_id} at {addr}")
        
        if node_id in self.nodes:
            with self.lock:
                self.last_heartbeat[node_id] = time.time()
                print(f"[DEBUG] Updated heartbeat for node {node_id}")
            self._send_response({'status': 'success'}, addr)
        else:
            print(f"[WARNING] Heartbeat received from unregistered node {node_id}")
            self._send_response({
                'status': 'error',
                'message': 'Node not registered'
            }, addr)

    def _send_response(self, response: dict, addr: Tuple[str, int]):
        try:
            print(f"[DEBUG] Sending response to {addr}:")
            print(f"[DEBUG] Response content: {response}")
            self.socket.sendto(json.dumps(response).encode(), addr)
            print(f"[DEBUG] Response sent successfully")
        except Exception as e:
            print(f"[ERROR] Failed to send response to {addr}: {e}")
            print(f"[DEBUG] Error details: {str(e)}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Start the UDP registry server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    args = parser.parse_args()

    print(f"[DEBUG] Starting registry server with arguments: host={args.host}, port={args.port}")
    registry = UDPRegistry(args.host, args.port)
    try:
        registry.start()
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down registry server...")
        registry.stop()

if __name__ == '__main__':
    main()