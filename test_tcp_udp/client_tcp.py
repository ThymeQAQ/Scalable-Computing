import socket

server_ip = "10.6.55.173"  # 替换为本机的 IP 地址
server_port = 33002        # 端口号，确保与服务端一致

# 创建 TCP 套接字
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 连接到服务端
client_socket.connect((server_ip, server_port))

# 要发送的消息
message = "Hello from Raspberry Pi!"
client_socket.send(message.encode())  # 向服务器发送消息

# 接收服务器的响应
response = client_socket.recv(1024)
print(f"Received response from server: {response.decode()}")

client_socket.close()
