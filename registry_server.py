from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time

app = Flask(__name__)
CORS(app)

class Registry:
    def __init__(self):
        self.nodes = {}
        self.lock = threading.Lock()

    def register_node(self, node_id, node_ip, node_port):
        with self.lock:
            self.nodes[node_id] = (node_ip, node_port)

    def remove_node(self, node_id):
        with self.lock:
            if node_id in self.nodes:
                del self.nodes[node_id]

    def get_nodes(self):
        with self.lock:
            return dict(self.nodes)

registry = Registry()

@app.route('/register', methods=['POST'])
def register_node():
    try:
        data = request.json
        if not all(k in data for k in ['node_id', 'node_ip', 'node_port']):
            return jsonify({"error": "Missing required fields"}), 400

        node_id = data['node_id']
        node_ip = data['node_ip']
        node_port = data['node_port']

        registry.register_node(node_id, node_ip, node_port)
        print(f"[INFO] Node {node_id} registered successfully at {node_ip}:{node_port}")
        return jsonify({"message": f"Node {node_id} registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/nodes', methods=['GET'])
def list_nodes():
    try:
        return jsonify(registry.get_nodes()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Start the registry server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    args = parser.parse_args()

    print(f"[INFO] Registry server starting on http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port)

if __name__ == '__main__':
    main()
