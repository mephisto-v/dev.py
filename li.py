from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import threading
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
import pygetwindow as gw

app = Flask(__name__)

# Store connected clients
clients = {}

# This is for the file manager functionality
UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Webcam streaming
def stream_webcam():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

# Remote Desktop (screen streaming)
def stream_screen():
    while True:
        screenshot = ImageGrab.grab()
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        _, jpeg = cv2.imencode('.jpg', img)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/client_list')
def client_list():
    return jsonify(list(clients.keys()))

@app.route('/start_stream')
def start_stream():
    return app.response_class(stream_screen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_webcam')
def start_webcam():
    return app.response_class(stream_webcam(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/send_command', methods=['POST'])
def send_command():
    command = request.form.get('command')
    result = os.popen(command).read()
    return jsonify(result=result)

@app.route('/file_upload', methods=['POST'])
def file_upload():
    file = request.files['file']
    file.save(os.path.join(UPLOAD_FOLDER, file.filename))
    return jsonify(success=True)

@app.route('/download_file/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/control', methods=['POST'])
def control():
    action = request.form.get('action')
    if action == 'move_mouse':
        x = int(request.form.get('x'))
        y = int(request.form.get('y'))
        pyautogui.moveTo(x, y)
    elif action == 'click':
        pyautogui.click()
    elif action == 'key_press':
        key = request.form.get('key')
        pyautogui.press(key)
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3389, debug=True)
