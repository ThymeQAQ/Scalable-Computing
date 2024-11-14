import sys
from tcp_p2p.node import Node
import socket

def send_message(node_id, node_ip, node_port, connections, target_node, message, broadcast=False):
    # 创建节点（不会启动接收服务，只作为发送工具）
    node = Node(node_id, node_ip, node_port)

    # 连接到其他节点
    for conn_id, (conn_ip, conn_port) in connections.items():
        if conn_id not in node.connections:
            try:
                node.connections[conn_id] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                node.connections[conn_id].connect((conn_ip, conn_port))
                node.connections[conn_id].sendall(node_id.encode())
            except Exception as e:
                print(f"Failed to connect to {conn_id} at {conn_ip}:{conn_port} - {e}")

    # 发送消息
    if broadcast:
        for conn_id, conn in node.connections.items():
            try:
                conn.sendall(f"{node_id} (broadcast): {message}".encode())
            except Exception as e:
                print(f"Error sending broadcast message to {conn_id}: {e}")
    else:
        if target_node in node.connections:
            try:
                node.connections[target_node].sendall(f"{node_id} (direct): {message}".encode())
            except Exception as e:
                print(f"Error sending direct message to {target_node}: {e}")
        else:
            print(f"No connection to node {target_node} for direct message.")

if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: python send_message.py <node_id> <node_ip> <node_port> <broadcast|direct> <target_node> <message> <conn_id:conn_ip:conn_port> ...")
        sys.exit(1)

    node_id = sys.argv[1]
    node_ip = sys.argv[2]
    node_port = int(sys.argv[3])
    mode = sys.argv[4]
    target_node = sys.argv[5] if mode == "direct" else None
    message = sys.argv[6]
    connections = {}
    for conn_arg in sys.argv[7:]:
        conn_id, conn_ip, conn_port = conn_arg.split(":")
        connections[conn_id] = (conn_ip, int(conn_port))

    send_message(node_id, node_ip, node_port, connections, target_node, message, broadcast=(mode == "broadcast"))
