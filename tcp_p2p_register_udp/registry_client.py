import socket
import json
import threading
import time
from typing import Dict, Tuple, Optional

class RegistryClient:
    def __init__(self, registry_host: str, registry_port: int, timeout: int = 10):
        self.registry_host = registry_host
        self.registry_port = registry_port
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self._heartbeat_thread = None
        self._is_running = False
        self._registered_node_id = None
        print(f"[DEBUG] Initialized RegistryClient with host={registry_host}, port={registry_port}")

    def register_node(self, node_id: str, node_port: int) -> bool:
        request = {
            'command': 'register',
            'node_id': node_id,
            'node_port': node_port
        }
        print(f"[DEBUG] Attempting to register node {node_id} on port {node_port}")
        response = self._send_request(request)
        if response and response.get('status') == 'success':
            self._registered_node_id = node_id
            print(f"[DEBUG] Node {node_id} registration successful")
            self._start_heartbeat()
            return True
        print(f"[DEBUG] Node {node_id} registration failed")
        return False

    def unregister_node(self, node_id: str) -> bool:
        request = {
            'command': 'unregister',
            'node_id': node_id
        }
        print(f"[DEBUG] Attempting to unregister node {node_id}")
        response = self._send_request(request)
        if response and response.get('status') == 'success':
            self._stop_heartbeat()
            print(f"[DEBUG] Node {node_id} unregistered successfully")
            return True
        return False

    def get_nodes(self) -> Dict[str, Tuple[str, int]]:
        request = {'command': 'get_nodes'}
        print("[DEBUG] Requesting list of registered nodes")
        response = self._send_request(request)
        if response and response.get('status') == 'success':
            nodes = response.get('nodes', {})
            print(f"[DEBUG] Retrieved {len(nodes)} registered nodes")
            return nodes
        print("[DEBUG] Failed to retrieve nodes list")
        return {}

    def _send_request(self, request: dict, retries: int = 5) -> Optional[dict]:
        last_exception = None
        for attempt in range(retries):
            try:
                print(f"[DEBUG] Sending request to {self.registry_host}:{self.registry_port} (Attempt {attempt + 1}/{retries})")
                print(f"[DEBUG] Request content: {request}")
                
                self.socket.sendto(
                    json.dumps(request).encode(),
                    (self.registry_host, self.registry_port)
                )
                
                print(f"[DEBUG] Waiting for response...")
                data, addr = self.socket.recvfrom(4096)
                
                print(f"[DEBUG] Received response from {addr}")
                response = json.loads(data.decode())
                print(f"[DEBUG] Response content: {response}")
                
                return response
                
            except socket.timeout as e:
                last_exception = e
                print(f"[DEBUG] Timeout on attempt {attempt + 1}: {e}")
            except json.JSONDecodeError as e:
                last_exception = e
                print(f"[DEBUG] JSON decode error on attempt {attempt + 1}: {e}")
            except Exception as e:
                last_exception = e
                print(f"[DEBUG] Unexpected error on attempt {attempt + 1}: {e}")
                
            if attempt < retries - 1:
                wait_time = 2 * (attempt + 1)  # Exponential backoff
                print(f"[DEBUG] Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] All {retries} attempts failed. Last error: {last_exception}")
        
        return None

    def _start_heartbeat(self):
        if self._heartbeat_thread is None and self._registered_node_id:
            print(f"[DEBUG] Starting heartbeat thread for node {self._registered_node_id}")
            self._is_running = True
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop)
            self._heartbeat_thread.daemon = True
            self._heartbeat_thread.start()

    def _stop_heartbeat(self):
        print("[DEBUG] Stopping heartbeat thread")
        self._is_running = False
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2)
            self._heartbeat_thread = None
        print("[DEBUG] Heartbeat thread stopped")

    def _heartbeat_loop(self):
        while self._is_running and self._registered_node_id:
            try:
                print(f"[DEBUG] Sending heartbeat for node {self._registered_node_id}")
                request = {
                    'command': 'heartbeat',
                    'node_id': self._registered_node_id
                }
                response = self._send_request(request)
                if response and response.get('status') == 'success':
                    print("[DEBUG] Heartbeat successful")
                else:
                    print("[WARNING] Heartbeat failed")
                    
                # Wait for next heartbeat
                for _ in range(30):  # 30 second interval split into 1-second checks
                    if not self._is_running:
                        return
                    time.sleep(1)
                    
            except Exception as e:
                print(f"[ERROR] Heartbeat failed: {e}")
                time.sleep(5)  # Wait a bit before retry if there's an error

    def close(self):
        print("[DEBUG] Closing registry client")
        self._stop_heartbeat()
        if self._registered_node_id:
            self.unregister_node(self._registered_node_id)
        self.socket.close()
        print("[DEBUG] Registry client closed")

def get_registry_connection():
    """Helper function to get registry connection parameters from environment"""
    import os
    host = os.getenv('REGISTRY_HOST', 'localhost')
    port = int(os.getenv('REGISTRY_PORT', '5000'))
    print(f"[DEBUG] Registry connection parameters: host={host}, port={port}")
    return (host, port)