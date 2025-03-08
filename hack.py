import socket

class Client:
    def __init__(self):
        self.server_ip = '127.0.0.1'
        self.server_port = 12345
        self.connect_to_server()

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.server_port))
        print("CONNECTED TO SERVER")
        self.handle_server_messages()

    def handle_server_messages(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if data:
                    # Handle server commands here
                    pass
            except:
                break

if __name__ == "__main__":
    client = Client()
