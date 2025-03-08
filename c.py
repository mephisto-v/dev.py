import requests
import cv2
import numpy as np
import pyautogui

SERVER_URL = "http://10.0.1.33:3389"

# Connect to the server and fetch the screen stream
def stream_screen():
    response = requests.get(f"{SERVER_URL}/start_stream", stream=True)
    bytes_data = b""
    for chunk in response.iter_content(chunk_size=1024):
        bytes_data += chunk
        a = bytes_data.find(b"\xff\xd8")
        b = bytes_data.find(b"\xff\xd9")
        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]
            img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            cv2.imshow("Remote Screen", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()

# Connect to the server and fetch webcam stream
def stream_webcam():
    response = requests.get(f"{SERVER_URL}/start_webcam", stream=True)
    bytes_data = b""
    for chunk in response.iter_content(chunk_size=1024):
        bytes_data += chunk
        a = bytes_data.find(b"\xff\xd8")
        b = bytes_data.find(b"\xff\xd9")
        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]
            img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            cv2.imshow("Remote Webcam", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    cv2.destroyAllWindows()

# Send mouse movement action
def move_mouse(x, y):
    requests.post(f"{SERVER_URL}/control", data={"action": "move_mouse", "x": x, "y": y})

# Send key press action
def key_press(key):
    requests.post(f"{SERVER_URL}/control", data={"action": "key_press", "key": key})

if __name__ == "__main__":
    # Example: Stream screen and webcam
    stream_screen()
    stream_webcam()
