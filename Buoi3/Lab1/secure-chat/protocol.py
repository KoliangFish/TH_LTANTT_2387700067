"""Length-prefixed JSON: TCP recv() does not preserve message boundaries."""
import json
import struct

MAX_FRAME = 65536


def read_exact(sock, size):
    result = bytearray()
    while len(result) < size:
        block = sock.recv(size - len(result))
        if not block:
            raise EOFError('Connection closed')
        result.extend(block)
    return bytes(result)


def receive(sock):
    size = struct.unpack('!I', read_exact(sock, 4))[0]
    if not 0 < size <= MAX_FRAME:
        raise ValueError('Invalid frame size')
    data = json.loads(read_exact(sock, size))
    if not isinstance(data, dict):
        raise ValueError('Expected JSON object')
    return data


def send(sock, data):
    payload = json.dumps(data, ensure_ascii=False).encode()
    if len(payload) > MAX_FRAME:
        raise ValueError('Message too large')
    sock.sendall(struct.pack('!I', len(payload)) + payload)
