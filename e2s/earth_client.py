import subprocess
import socket
import time
import numpy as np
import threading
import psutil
import zlib  # 引入zlib库

# 计算CRC32校验和
def checksum(data):
    return zlib.crc32(data) & 0xFFFFFFFF  # 返回32位CRC校验和

def start_clumsy(single_latency, single_drop_rate):
    CLUM_DIR = "clumsy"
    cmd = f"clumsy.exe --drop on --drop-inbound on --drop-outbound on --drop-chance {single_drop_rate} " \
          f"--lag on --lag-inbound on --lag-outbound on --lag-time {single_latency}"
    process = subprocess.Popen(cmd, cwd=CLUM_DIR, shell=True)
    print("clumsy started.")
    return process.pid


def kill_clumsy(pid):
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.kill()
    parent.kill()
    print("clumsy stopped.")


def clumsy_simulate(server_addr, buffer_size, timeout, self_ll, self_node_num):
    inquire_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inquire_socket.settimeout(timeout)
    self_lat, self_lon = self_ll
    clumsy_pid = None
    while True:
        flag = 0
        pn, tp, cu = 0, 0, 0
        header = flag.to_bytes(4, 'big') + self_node_num.to_bytes(4, 'big') \
                 + pn.to_bytes(4, 'big') + tp.to_bytes(4, 'big')
        inquiry = header + cu.to_bytes(4, 'big')
        
        # 计算CRC32校验和并附加到数据包
        checksum_value = checksum(inquiry)
        inquiry_with_checksum = inquiry + checksum_value.to_bytes(4, 'big')  # 使用4个字节存储校验和

        try:
            inquire_socket.sendto(inquiry_with_checksum, server_addr)
            ack, _ = inquire_socket.recvfrom(buffer_size)
            
            # 校验校验和
            received_checksum = int.from_bytes(ack[-4:], 'big')  # 提取校验和
            data_without_checksum = ack[:-4]
            if checksum(data_without_checksum) != received_checksum:
                print("Checksum mismatch, packet may be corrupted!")
                continue

            flag, node_number, lat_info, lon_info = ack[:4], ack[4:8], ack[8:12], ack[12:16]
            flag = int.from_bytes(flag, 'big')
            assert flag == 0, "Received wrong acknowledgement for latitude/longitude inquiry"
            node_number = int.from_bytes(node_number, 'big')
            sat_lat = int.from_bytes(lat_info, 'big', signed=True)
            sat_lon = int.from_bytes(lon_info, 'big', signed=True)
            print(f"Received data for latitude {sat_lat}, longitude {sat_lon}")
            if clumsy_pid is not None:
                kill_clumsy(clumsy_pid)
            clumsy_pid = start_clumsy(single_latency, single_drop_rate)

        except socket.timeout:
            pass
        time.sleep(3)


def client(server_addr, buffer_size, timeout, debug_interval, chunk_size, self_node_num):
    message = "This is a test string that will be sent as binary data over UDP in smaller packets."
    binary_stream = message.encode('utf-8')
    chunks = [binary_stream[i:i + chunk_size] for i in range(0, len(binary_stream), chunk_size)]
    total_packets = len(chunks)
    total_send = 0
    rtts = []

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)

    for packet_number, chunk in enumerate(chunks):
        flag = 1
        header = flag.to_bytes(4, 'big') + self_node_num.to_bytes(4, 'big') \
                 + packet_number.to_bytes(4, 'big') + total_packets.to_bytes(4, 'big')
        packet = header + chunk
        
        # 计算CRC32校验和并附加到数据包
        checksum_value = checksum(packet)
        packet_with_checksum = packet + checksum_value.to_bytes(4, 'big')  # 使用4个字节存储校验和

        while True:
            try:
                total_send += 1
                start_time = time.time()
                client_socket.sendto(packet_with_checksum, server_addr)
                ack, _ = client_socket.recvfrom(buffer_size)
                end_time = time.time()
                rtt = (end_time - start_time) * 1000
                rtts.append(rtt)

                # 校验校验和
                received_checksum = int.from_bytes(ack[-4:], 'big')  # 提取校验和
                data_without_checksum = ack[:-4]
                if checksum(data_without_checksum) != received_checksum:
                    print("Checksum mismatch, packet may be corrupted!")
                    continue

                ack_number = int.from_bytes(ack, 'big')
                break
            except socket.timeout:
                print(f"Timeout: packet_num={packet_number}, resending...")
            time.sleep(debug_interval)

        time.sleep(debug_interval)

    print(f"Packets transmitted: {total_send}, Packets received: {len(rtts)}")

if __name__ == "__main__":
    SERVER_ADDR = ('localhost', 8080)
    BUFFER_SIZE = 1024
    EARTH_LL = (0, -180)
    EARTH_NODE_NUM = 10
    TIMEOUT = 2
    DEBUG_INTER = 1
    CHUNK_SIZE = 10

    # Start threads
    clumsy_thread = threading.Thread(target=clumsy_simulate, args=(SERVER_ADDR, BUFFER_SIZE, TIMEOUT, EARTH_LL, EARTH_NODE_NUM), daemon=True)
    client_thread = threading.Thread(target=client, args=(SERVER_ADDR, BUFFER_SIZE, TIMEOUT, DEBUG_INTER, CHUNK_SIZE, EARTH_NODE_NUM), daemon=True)

    clumsy_thread.start()
    client_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting..")
