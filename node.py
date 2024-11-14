import socket
import threading

class Node:
    def __init__(self, node_id, host, port):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.connections = {}  # key: node_id, value: socket
        self.is_running = False

    def start(self):
        self.is_running = True
        self.server_thread = threading.Thread(target=self.server_loop)
        self.server_thread.start()

    def stop(self):
        self.is_running = False
        self.server_thread.join()
        # Gracefully close all connections when stopping
        for conn in self.connections.values():
            conn.close()

    def server_loop(self):
        # 创建服务器 socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)  # 可以监听多个连接，设置队列大小为 5
        print(f"[DEBUG] Node {self.node_id} listening on {self.host}:{self.port}")

        while self.is_running:
            try:
                # 等待多个连接
                conn, addr = server_socket.accept()
                print(f"[DEBUG] Node {self.node_id} connected to {addr}")

                # 接收节点 ID
                node_id = conn.recv(1024).decode()
                self.connections[node_id] = conn
                print(f"[DEBUG] Node {self.node_id} received connection from {node_id}")

                # 启动一个线程来接收消息
                recv_thread = threading.Thread(target=self.receive_messages, args=(node_id, conn))
                recv_thread.start()
            except Exception as e:
                print(f"[ERROR] Node {self.node_id} encountered an error: {e}")

        # 在 while 循环退出后可以选择关闭服务器 socket
        server_socket.close()

    def receive_messages(self, node_id, conn):
        try:
            while self.is_running:
                # 接收消息直到连接关闭
                message = conn.recv(1024).decode()
                if message:
                    print(f"[DEBUG] Message from {node_id}: {message}")
                else:
                    print(f"[DEBUG] Node {node_id} has closed the connection.")
                    break  # 如果连接关闭，则退出循环
        except Exception as e:
            print(f"[ERROR] Error receiving message from {node_id}: {e}")
        finally:
            # 在连接断开时移除该连接
            if node_id in self.connections:
                del self.connections[node_id]
            conn.close()

    def send_direct(self, target_node_id, message):
        if target_node_id in self.connections:
            try:
                self.connections[target_node_id].sendall(message.encode())
                print(f"[DEBUG] Sent message to {target_node_id}: {message}")
            except Exception as e:
                print(f"[ERROR] Error sending message to {target_node_id}: {e}")
        else:
            print(f"[ERROR] Connection to {target_node_id} not found.")
