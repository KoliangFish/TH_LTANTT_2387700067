import argparse
import base64
import logging
import socket
import ssl
import threading
from pathlib import Path
from connection_manager import ConnectionManager
from room_manager import RoomManager
from protocol import receive

ROOT = Path(__file__).resolve().parent
LOG = logging.getLogger('securechat')


class SecureChatServer:
    def __init__(self, host='127.0.0.1', port=8443, root=ROOT):
        root = Path(root)
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.context.load_cert_chain(root / 'certs/server/server.crt', root / 'certs/server/server.key')
        self.context.load_verify_locations(root / 'certs/ca/ca.crt')
        self.context.verify_mode = ssl.CERT_REQUIRED
        self.connections = ConnectionManager()
        self.rooms = RoomManager()
        self.stop_event = threading.Event()
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((host, port))
        self.listener.listen(20)
        self.listener.settimeout(.2)
        self.port = self.listener.getsockname()[1]

    def serve_forever(self):
        LOG.info('Listening 127.0.0.1:%s; mTLS required', self.port)
        while not self.stop_event.is_set():
            try:
                raw, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self.handle, args=(raw,), daemon=True).start()

    def handle(self, raw):
        sock = raw
        try:
            raw.settimeout(10)
            sock = self.context.wrap_socket(raw, server_side=True)
            identity = next(value for attrs in sock.getpeercert()['subject']
                            for key, value in attrs if key == 'commonName')
            self.connections.add_client(sock, identity)
            self.connections.send_to(sock, {'type': 'welcome', 'username': identity})
            room = 'general'
            self.rooms.join_room(room, sock)
            sock.settimeout(300)
            LOG.info('Authenticated client=%s TLS=%s', identity, sock.version())
            while True:
                data = receive(sock)
                if data.get('type') == 'join':
                    room = data.get('room')
                    self.rooms.join_room(room, sock)
                    self.connections.send_to(sock, {'type': 'joined', 'room': room})
                elif data.get('type') == 'message':
                    token = data.get('ciphertext')
                    if not isinstance(token, str) or len(base64.b64decode(token, validate=True)) < 28:
                        raise ValueError('Invalid encrypted message')
                    LOG.info('Relay client=%s room=%s ciphertext_bytes=%s', identity, room, len(token))
                    for other in self.rooms.members(room):
                        if other != sock:
                            try:
                                self.connections.send_to(other, {'type': 'message', 'sender': identity,
                                                                 'room': room, 'ciphertext': token})
                            except OSError:
                                other.close()
                else:
                    raise ValueError('Unknown command')
        except (OSError, ValueError, EOFError, KeyError, StopIteration) as exc:
            LOG.info('Connection ended/rejected: %s', exc)
        finally:
            self.rooms.leave(sock)
            self.connections.remove_client(sock)
            sock.close()

    def stop(self):
        self.stop_event.set()
        self.listener.close()
        with self.connections.lock:
            clients = list(self.connections.clients)
        for sock in clients:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8443)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s',
                        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / 'securechat.log', encoding='utf-8')])
    server = SecureChatServer(port=args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
