import sys
from tcp_p2p.node import Node
import socket

def main(node_id, node_ip, node_port, connections):
    # 创建节点
    node = Node(node_id, node_ip, node_port)

    # 启动节点
    node.start()

    # 连接到其他节点
    for conn_id, (conn_ip, conn_port) in connections.items():
        try:
            # 创建套接字并连接
            node.connections[conn_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            node.connections[conn_id].connect((conn_ip, conn_port))
            node.connections[conn_id].sendall(node_id.encode())
            print(f"{node_id} connected to {conn_id} at {conn_ip}:{conn_port}")
        except Exception as e:
            print(f"Failed to connect to {conn_id} at {conn_ip}:{conn_port} - {e}")

    print(f"{node_id} is ready. Use 'send_message.py' to send messages.")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python main.py <node_id> <node_ip> <node_port> <conn_id1:conn_ip1:conn_port1> <conn_id2:conn_ip2:conn_port2> ...")
        sys.exit(1)

    node_id = sys.argv[1]
    node_ip = sys.argv[2]
    node_port = int(sys.argv[3])

    connections = {}
    for conn_arg in sys.argv[4:]:
        conn_id, conn_ip, conn_port = conn_arg.split(":")
        connections[conn_id] = (conn_ip, int(conn_port))

    main(node_id, node_ip, node_port, connections)
