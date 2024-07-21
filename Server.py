import socket
import sys
import struct
import threading
import signal
from PyQt5.QtCore import QCoreApplication, QObject, pyqtSignal

file_name = input('Enter the desired file:')
buffer_size = int(input('Enter the size of each sample to be transferred at a time:'))

class Server(QObject):
    signal_exit = pyqtSignal()

    def __init__(self):
        super(Server, self).__init__()
        self.host = '127.0.0.1'
        self.port = 12345
        self.server_socket = None

    def send_binary_file(self, conn):
        file_path = file_name
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                conn.sendall(data)

    def handle_client(self, client_socket):
        self.send_binary_file(client_socket)
        client_socket.close()

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        print("Server listening on {}:{}".format(self.host, self.port))
        client_socket, addr = self.server_socket.accept()
        print("Connected with {}:{}".format(addr[0], addr[1]))

        client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
        client_handler.start()

        self.signal_exit.connect(self.stop_server)

    def stop_server(self):
        if self.server_socket:
            self.server_socket.close()
            print("Server socket closed.")
        QCoreApplication.quit()

def exit_handler(*args):
    server.signal_exit.emit()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, exit_handler)

    app = QCoreApplication([])
    server = Server()
    server.start_server()
    sys.exit(app.exec_())
