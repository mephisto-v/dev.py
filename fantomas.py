import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel
from PyQt5.QtCore import Qt
import pickle
import cv2
import numpy as np

# Server GUI class to manage clients and control features
class TeamViewer2Server(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TeamViewer 2 Server")
        self.setGeometry(100, 100, 600, 400)

        # Client list widget
        self.client_list_widget = QListWidget(self)
        self.client_list_widget.setGeometry(10, 10, 380, 200)

        # Connect button
        self.connect_button = QPushButton("Connect to Clients", self)
        self.connect_button.setGeometry(10, 220, 380, 40)
        self.connect_button.clicked.connect(self.connect_clients)

        # Start remote desktop
        self.start_rd_button = QPushButton("Start Remote Desktop", self)
        self.start_rd_button.setGeometry(10, 270, 380, 40)
        self.start_rd_button.clicked.connect(self.start_remote_desktop)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.client_list_widget)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.start_rd_button)

        self.setLayout(layout)

    def connect_clients(self):
        """Start listening for incoming client connections."""
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('0.0.0.0', 4782))
        self.server.listen(5)
        print("Server listening on port 4782...")
        threading.Thread(target=self.accept_connections).start()

    def accept_connections(self):
        """Accept incoming client connections and handle them."""
        while True:
            client_socket, addr = self.server.accept()
            print(f"Connection from {addr} established!")
            self.client_list_widget.addItem(f"Client {addr}")

            # No encryption used
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

    def handle_client(self, client_socket, addr):
        """Handle incoming requests from the client (e.g., file management, remote shell, etc.)."""
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                print(f"Data from client {addr}: {data.decode()}")
                # Process different requests: file management, shell, remote desktop, etc.
            except Exception as e:
                print(f"Error: {e}")
                break

    def start_remote_desktop(self):
        """Start the remote desktop feature to view and control the client screen."""
        print("Starting Remote Desktop...")

# Initialize and run the server
if __name__ == '__main__':
    app = QApplication(sys.argv)
    server = TeamViewer2Server()
    server.show()
    sys.exit(app.exec_())
