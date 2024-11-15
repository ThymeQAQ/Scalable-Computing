import socket

host = "0.0.0.0"  # 本机绑定到所有网络接口
port = 33001      # 端口号，确保树莓派和本机使用相同的端口号

# 创建 TCP 套接字
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(1)  # 最大连接数为1，表示只接受一个客户端连接

print(f"TCP server is listening on port {port}...")

# 接受客户端的连接
client_socket, client_address = server_socket.accept()
print(f"Connection from {client_address} established.")

# 接收数据并发送响应
while True:
    data = client_socket.recv(1024)  # 接收客户端发送的数据，最大1024字节
    if not data:
        break  # 如果没有数据，退出循环
    print(f"Received message: {data.decode()}")

    # 向客户端发送响应
    response = "Message received by server!"
    client_socket.send(response.encode())

# 关闭连接
client_socket.close()
server_socket.close()
