import threading
from protocol import send


class ConnectionManager:
    def __init__(self):
        self.clients = {}
        self.lock = threading.RLock()

    def add_client(self, sock, username):
        with self.lock:
            if username in [info['username'] for info in self.clients.values()]:
                raise ValueError('Identity already connected')
            self.clients[sock] = {'username': username, 'send_lock': threading.Lock()}

    def remove_client(self, sock):
        with self.lock:
            self.clients.pop(sock, None)

    def send_to(self, sock, data):
        with self.lock:
            info = self.clients.get(sock)
        if info:
            with info['send_lock']:
                send(sock, data)
