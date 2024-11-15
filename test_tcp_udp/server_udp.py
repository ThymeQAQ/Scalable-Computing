import socket

host = "0.0.0.0" 
port = 33002     

# 创建 UDP 套接字
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((host, port))

print(f"UDP server is listening on port {port}...")

while True:
    data, client_address = server_socket.recvfrom(1024)  # 接收来自客户端的数据，最大1024字节
    print(f"Received message from {client_address}: {data.decode()}")

    # 向客户端发送响应
    response = "Message received by server!"
    server_socket.sendto(response.encode(), client_address)
