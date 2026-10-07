import argparse
import base64
import json
import socket
import ssl
import threading
from pathlib import Path
from cryptography.exceptions import InvalidTag
from message_encryption import MessageEncryption
from protocol import receive, send

ROOT = Path(__file__).resolve().parent


class SecureChatClient:
    def __init__(self, username, host='127.0.0.1', port=8443, root=ROOT, server_name=None):
        if username not in ('alice', 'bob', 'charlie'):
            raise ValueError('Choose alice, bob or charlie')
        root = Path(root)
        self.keys = json.loads((root / 'room_keys.json').read_text(encoding='utf-8'))
        context = ssl.create_default_context(cafile=str(root / 'certs/ca/ca.crt'))
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(root / f'certs/client/{username}.crt', root / f'certs/client/{username}.key')
        raw = socket.create_connection((host, port), timeout=5)
        try:
            self.sock = context.wrap_socket(raw, server_hostname=server_name or host)
            self.welcome = receive(self.sock)
        except Exception:
            raw.close()
            raise
        self.room = 'general'
        self.sock.settimeout(None)
        self.send_lock = threading.Lock()

    def join(self, room):
        if room not in self.keys:
            raise ValueError('No local key for this room')
        with self.send_lock:
            send(self.sock, {'type': 'join', 'room': room})
        self.room = room

    def send_message(self, text):
        cipher = MessageEncryption(base64.b64decode(self.keys[self.room]))
        with self.send_lock:
            send(self.sock, {'type': 'message', 'ciphertext': cipher.encrypt(text, self.room)})

    def receive_message(self):
        data = receive(self.sock)
        if data['type'] == 'message':
            cipher = MessageEncryption(base64.b64decode(self.keys[data['room']]))
            data['text'] = cipher.decrypt(data['ciphertext'], data['room'])
        return data

    def close(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', choices=['alice', 'bob', 'charlie'], required=True)
    parser.add_argument('--port', type=int, default=8443)
    args = parser.parse_args()
    client = SecureChatClient(args.username, port=args.port)
    print(f"Verified server; {client.sock.version()}; identity={client.welcome['username']}")
    print('Type message, /join general, /join study, /quit')

    def read():
        try:
            while True:
                try:
                    data = client.receive_message()
                    print(f"[{data['room']}] {data['sender']}: {data['text']}" if data['type'] == 'message' else data)
                except (InvalidTag, ValueError):
                    print('Rejected message: wrong key or modified ciphertext')
        except (OSError, EOFError):
            print('Disconnected')

    threading.Thread(target=read, daemon=True).start()
    try:
        while True:
            text = input()
            if text in ('/quit', 'exit'):
                break
            try:
                if text.startswith('/join '):
                    client.join(text[6:].strip())
                elif text:
                    client.send_message(text)
            except ValueError as exc:
                print(exc)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        client.close()


if __name__ == '__main__':
    main()
