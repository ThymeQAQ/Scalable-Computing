import socket
import time
import hashlib

def calculate_checksum(data):
    # 计算数据的校验和
    checksum = hashlib.md5(data).hexdigest()
    return checksum.encode('utf-8')

if __name__ == "__main__":
    # 配置
    SERVER_ADDR = ('localhost', 8080)
    BUFFER_SIZE = 1024
    CHUNK_SIZE = 10  # 数据包大小
    TIMEOUT = 1  # 1秒的超时时间
    DEBUG_INTERVAL = 1  # 调试发送间隔

    # 从终端获取自定义消息
    message = input("Please input the message: ")
    binary_stream = message.encode('utf-8')  # 编码为字节流
    chunks = [binary_stream[i:i+CHUNK_SIZE] for i in range(0, len(binary_stream), CHUNK_SIZE)]
    total_packets = len(chunks)

    # 创建UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.settimeout(TIMEOUT)  # 设置超时时间
        print(f"\nSending udp://{SERVER_ADDR[0]}:{SERVER_ADDR[1]} with {total_packets} packets:\n")

        for packet_number, chunk in enumerate(chunks):
            # 构建数据包头：数据包号 (32-bit)，总数据包数 (32-bit)
            header = packet_number.to_bytes(4, 'big') + total_packets.to_bytes(4, 'big')
            checksum = calculate_checksum(header + chunk)
            packet = header + checksum + chunk
            print(f"Sent packet {packet_number}/{total_packets}")
            while True:
                try:
                    # 发送数据包
                    client_socket.sendto(packet, SERVER_ADDR)
                    # 等待确认
                    ack, _ = client_socket.recvfrom(BUFFER_SIZE)
                    ack_number = int.from_bytes(ack, 'big')
                    print(f"Received ACK: packet_num={ack_number}")
                    break
                except socket.timeout:
                    print(f"Timeout: packet_num={packet_number}, resending...")
                time.sleep(DEBUG_INTERVAL)
