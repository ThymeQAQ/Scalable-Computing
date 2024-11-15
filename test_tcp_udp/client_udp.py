import socket

server_ip = "10.35.70.10"  # 替换为树莓派的 IP 地址
server_port = 33002           # 使用与服务器相同的端口号

# 创建 UDP 套接字
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# 要发送的消息
message = "Hello from client!"
client_socket.sendto(message.encode(), (server_ip, server_port))

# 接收服务器的响应
response, server_address = client_socket.recvfrom(1024)
print(f"Received response from server: {response.decode()}")

client_socket.close()
