import socket
import hashlib

def calculate_checksum(data):
    # 计算数据的校验和
    checksum = hashlib.md5(data).hexdigest()
    return checksum.encode('utf-8')

if __name__ == "__main__":
    # Configuration
    SERVER_ADDR = ('localhost', 8080)
    BUFFER_SIZE = 1024

    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind(SERVER_ADDR)
        print(f"Server is listening on {SERVER_ADDR[0]}:{SERVER_ADDR[1]}...")

        received_packets = {}
        total_packets = None  # Total packets to expect

        while True:
            # Receive a packet
            data, client_address = server_socket.recvfrom(BUFFER_SIZE)

            # Decode the packet
            packet_number = int.from_bytes(data[:4], 'big')
            total_packets = int.from_bytes(data[4:8], 'big')
            checksum = data[8:40]  # MD5 checksum is 32 bytes
            chunk = data[40:]

            # Verify checksum
            calculated_checksum = calculate_checksum(data[:8] + chunk)
            if checksum != calculated_checksum:
                print(f"Checksum mismatch for packet {packet_number}. Ignoring.")
                continue

            # Store the packet content
            received_packets[packet_number] = chunk
            print(f"Received packet {packet_number}/{total_packets} from {client_address}")

            # Send acknowledgment for the received packet
            ack = packet_number.to_bytes(4, 'big')
            server_socket.sendto(ack, client_address)

            # If all packets are received, reassemble the binary stream
            if len(received_packets) == total_packets:
                print("All packets received!")
                # Reassemble and decode the original string
                binary_stream = b''.join(received_packets[i] for i in range(total_packets))
                original_string = binary_stream.decode()
                print("Reconstructed String:", original_string)
