"""AES-256-GCM: room keys stay on clients; authenticate the room name."""
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class MessageEncryption:
    def __init__(self, key):
        if len(key) != 32:
            raise ValueError('AES-256 requires 32 bytes')
        self.cipher = AESGCM(key)

    def encrypt(self, plaintext, room='general'):
        nonce = os.urandom(12)
        data = nonce + self.cipher.encrypt(nonce, plaintext.encode(), room.encode())
        return base64.b64encode(data).decode('ascii')

    def decrypt(self, token, room='general'):
        data = base64.b64decode(token, validate=True)
        return self.cipher.decrypt(data[:12], data[12:], room.encode()).decode()
