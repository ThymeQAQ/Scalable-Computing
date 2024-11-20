import socket
import threading
import time
from collections import deque
import zlib  # 引入zlib库

# 计算CRC32校验和
def checksum(data):
    return zlib.crc32(data) & 0xFFFFFFFF  # 返回32位CRC校验和

def keep_moving(global_dequeue, orbit_z_axis, num_sats, velocity, sat_index):
    # 模拟卫星运动
    sat_ll_list = init_satellites(orbit_z_axis, num_sats)
    (lat, lon) = sat_ll_list[sat_index]
    start_time = time.time()
    
    while True:
        time.sleep(1)
        end_time = time.time()
        t = end_time - start_time
        start_time = end_time
        lat, lon = satellites_move((lat, lon), orbit_z_axis, velocity, t)
        print(f"Satellites keeps moving: time slaps {t}, latitude {lat}, longitude {lon}")
        # 更新全局队列，方便多线程共享数据
        global_dequeue.append((lat, lon))

def server(global_dequeue, server_addr, buffer_size, sat_node_number):
    # 创建UDP服务器套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(server_addr)

    print(f"Satellite with node number {sat_node_number} is listening on {server_addr[0]}:{server_addr[1]}...")
    received_packets = {}

    while True:
        data, client_address = server_socket.recvfrom(buffer_size)
        print("Packet received!")

        # 校验校验和
        received_checksum = int.from_bytes(data[-4:], 'big')  # 提取校验和
        data_without_checksum = data[:-4]
        if checksum(data_without_checksum) != received_checksum:
            print("Checksum mismatch, packet may be corrupted!")
            continue

        flag, node_number, packet_number, total_packets, chunk = data[:4], data[4:8], data[8:12], data[12:16], data[16:]
        flag = int.from_bytes(flag, 'big')
        node_number = int.from_bytes(node_number, 'big')

        if flag == 0:
            try:
                lat, lon = global_dequeue.pop()
            except global_dequeue.Empty:
                lat, lon = -800, -800  # 如果队列为空，返回一个无效值
            lat_info = int(lat).to_bytes(4, 'big', signed=True)
            lon_info = int(lon).to_bytes(4, 'big', signed=True)
            ll_info = flag.to_bytes(4, 'big') + sat_node_number.to_bytes(4, 'big') + lat_info + lon_info
            
            # 计算CRC32校验和并附加到数据包
            checksum_value = checksum(ll_info)
            ll_info_with_checksum = ll_info + checksum_value.to_bytes(4, 'big')  # 使用4个字节存储校验和
            server_socket.sendto(ll_info_with_checksum, client_address)

        else:
            # 存储数据包内容
            if node_number in received_packets.keys():
                received_packets[node_number][packet_number] = chunk
            else:
                received_packets[node_number] = {packet_number: chunk}

            # 发送确认消息
            ack_packet = checksum(data).to_bytes(4, 'big')  # 包含校验和的确认消息
            server_socket.sendto(ack_packet, client_address)

            # 如果所有包都已接收，重新组装二进制流
            if len(received_packets[node_number]) == total_packets:
                print(f"All packets from node {node_number} received!")
                # 重新组装并解码原始字符串
                binary_stream = b''.join(received_packets[node_number][i] for i in range(total_packets))
                original_string = binary_stream.decode()
                print("Reconstructed String:", original_string)

if __name__ == "__main__":
    global_dequeue = deque(maxlen=10)
    SERVER_ADDR = ('localhost', 8080)
    BUFFER_SIZE = 1024
    NUM_SATS = 5
    SAT_INDEX = 0
    SAT_NODE_NUM = 0
    ORBIT_Z_AXIS = (0, 0)
    VELOCITY = 27000 / 111.3 / (60 * 60)
    print(f"velocity: {VELOCITY}")

    # 启动卫星运动线程
    simulation_thread = threading.Thread(target=keep_moving, args=(global_dequeue, ORBIT_Z_AXIS, NUM_SATS, VELOCITY, SAT_INDEX),
                                         daemon=True)
    # 启动服务器线程
    server_thread = threading.Thread(target=server, args=(global_dequeue, SERVER_ADDR, BUFFER_SIZE, SAT_NODE_NUM),
                                     daemon=True)

    # 启动线程
    simulation_thread.start()
    server_thread.start()

    # 保持主程序运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting..")
