# Test receiver (run separately)
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 11111))
print("Listening for video...")
while True:
    data, addr = sock.recvfrom(65535)
    print(f"Received {len(data)} bytes from {addr}")
