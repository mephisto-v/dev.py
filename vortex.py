import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import os
import subprocess

class ServerGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("TeamViewer 2 - Server")
        self.master.geometry("800x600")

        self.clients = {}

        self.create_widgets()
        self.start_server()

    def create_widgets(self):
        # Client list
        self.client_list_frame = ttk.LabelFrame(self.master, text="Connected Clients")
        self.client_list_frame.pack(fill="both", expand=True)
        self.client_listbox = tk.Listbox(self.client_list_frame)
        self.client_listbox.pack(fill="both", expand=True)

        # File Manager
        self.file_manager_frame = ttk.LabelFrame(self.master, text="File Manager")
        self.file_manager_frame.pack(fill="both", expand=True)
        self.file_manager_text = tk.Text(self.file_manager_frame)
        self.file_manager_text.pack(fill="both", expand=True)

        # Remote Desktop
        self.remote_desktop_frame = ttk.LabelFrame(self.master, text="Remote Desktop")
        self.remote_desktop_frame.pack(fill="both", expand=True)
        self.remote_desktop_text = tk.Text(self.remote_desktop_frame)
        self.remote_desktop_text.pack(fill="both", expand=True)

        # Remote Shell
        self.remote_shell_frame = ttk.LabelFrame(self.master, text="Remote Shell")
        self.remote_shell_frame.pack(fill="both", expand=True)
        self.remote_shell_text = tk.Text(self.remote_shell_frame)
        self.remote_shell_text.pack(fill="both", expand=True)
        self.remote_shell_entry = tk.Entry(self.remote_shell_frame)
        self.remote_shell_entry.pack(fill="both", expand=True)
        self.remote_shell_entry.bind("<Return>", self.send_remote_shell_command)

        # System Information
        self.system_info_frame = ttk.LabelFrame(self.master, text="System Information")
        self.system_info_frame.pack(fill="both", expand=True)
        self.system_info_text = tk.Text(self.system_info_frame)
        self.system_info_text.pack(fill="both", expand=True)

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 12345))
        self.server_socket.listen(5)
        threading.Thread(target=self.accept_clients).start()

    def accept_clients(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            self.clients[client_address] = client_socket
            self.client_listbox.insert(tk.END, str(client_address))
            threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()

    def handle_client(self, client_socket, client_address):
        while True:
            try:
                data = client_socket.recv(1024).decode()
                if data:
                    # Handle client messages here
                    pass
            except:
                del self.clients[client_address]
                self.client_listbox.delete(self.client_listbox.get(0, tk.END).index(str(client_address)))
                break

    def send_remote_shell_command(self, event):
        cmd = self.remote_shell_entry.get()
        self.remote_shell_entry.delete(0, tk.END)
        # Send command to selected client
        selected_client = self.client_listbox.get(tk.ACTIVE)
        client_socket = self.clients[eval(selected_client)]
        client_socket.send(cmd.encode())

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()
