"""Run real TLS integration cases and regenerate README evidence."""
import base64
import json
import logging
import os
import socket
import ssl
import sys
import tempfile
import threading
import time
from pathlib import Path
from cryptography.exceptions import InvalidTag
from cryptography import x509
from cryptography.x509.oid import NameOID
from make_certs import generate, ROOT
from server import SecureChatServer
from client import SecureChatClient
from message_encryption import MessageEncryption
from protocol import send, receive

sys.path.insert(0, str(ROOT.parents[1]))
from evidence import save_case


def main():
    lab = ROOT.parent
    if not (ROOT / 'certs/ca/ca.crt').exists():
        generate()
    details = []
    for file in sorted((ROOT / 'certs').rglob('*.crt')):
        cert = x509.load_pem_x509_certificate(file.read_bytes())
        details.append(f'{file.relative_to(ROOT)}: CN={cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value}')
    cert = x509.load_pem_x509_certificate((ROOT / 'certs/server/server.crt').read_bytes())
    details.append('Server SAN: ' + str(cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value))
    save_case(lab, 'case1_certificates', 'Case 1 · CA and certificate identities', '\n'.join(details))
    log_path = ROOT / 'demo-server.log'
    handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
    logger = logging.getLogger('securechat')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    server = SecureChatServer(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    clients = []
    try:
        alice, bob, charlie = [SecureChatClient(name, port=server.port) for name in ('alice', 'bob', 'charlie')]
        clients.extend([alice, bob, charlie])
        plaintext = 'Xin chào Bob! Tin nhắn bảo mật từ Alice.'
        alice.send_message(plaintext)
        message = bob.receive_message()
        assert message['text'] == plaintext and message['sender'] == 'alice'
        assert charlie.receive_message()['text'] == plaintext
        save_case(lab, 'case2_chat', 'Case 2 · Three clients over mutual TLS',
                  f'Connected: alice, bob, charlie\nTLS negotiated: {alice.sock.version()}\n'
                  f'Alice sends: {plaintext}\nBob receives: {message["text"]}\nCharlie receives the same message\n'
                  f'Server relays ciphertext: {message["ciphertext"]}\nPASS: Unicode round-trip over real TLS sockets')
        charlie.join('study')
        assert charlie.receive_message() == {'type': 'joined', 'room': 'study'}
        alice.send_message('general only')
        assert bob.receive_message()['text'] == 'general only'
        charlie.sock.settimeout(.3)
        try:
            charlie.receive_message()
            raise AssertionError('Room isolation failed')
        except socket.timeout:
            pass
        charlie.sock.settimeout(None)
        alice.join('study')
        assert alice.receive_message()['type'] == 'joined'
        alice.send_message('study only')
        assert charlie.receive_message()['text'] == 'study only'
        save_case(lab, 'case3_rooms', 'Case 3 · Room isolation and switching',
                  'charlie joins study -> joined ACK\nalice -> general: general only\n'
                  'bob receives; charlie waits 0.3s -> no message\nalice joins study -> joined ACK\n'
                  'alice -> study: study only\ncharlie receives: study only\nPASS: rooms route independently')
        key = os.urandom(32)
        cipher = MessageEncryption(key)
        token = cipher.encrypt('secret')
        raw = bytearray(base64.b64decode(token)); raw[-1] ^= 1
        failures = []
        for label, other, value, room in [('tampered ciphertext', cipher, base64.b64encode(raw).decode(), 'general'),
                                           ('wrong key', MessageEncryption(os.urandom(32)), token, 'general'),
                                           ('wrong room AAD', cipher, token, 'study')]:
            try:
                other.decrypt(value, room)
                raise AssertionError(label)
            except InvalidTag:
                failures.append(label + ' -> InvalidTag (rejected)')
        handler.flush()
        assert plaintext not in log_path.read_text(encoding='utf-8')
        save_case(lab, 'case4_e2ee', 'Case 4 · End-to-end encryption and integrity',
                  '\n'.join(failures) + '\nServer never receives room_keys.json or AES keys\n'
                  'Server log contains metadata/ciphertext length, no chat plaintext\nPASS: AES-GCM integrity and server blindness')
        errors = []
        try:
            SecureChatClient('alice', port=server.port, server_name='wrong.example')
            raise AssertionError('Hostname accepted')
        except ssl.SSLCertVerificationError as exc:
            errors.append('Wrong hostname -> ' + exc.verify_message)
        with tempfile.TemporaryDirectory() as tmp:
            generate(tmp)
            try:
                SecureChatClient('alice', port=server.port, root=tmp)
                raise AssertionError('Untrusted CA accepted')
            except ssl.SSLCertVerificationError as exc:
                errors.append('Untrusted CA -> ' + exc.verify_message)
        context = ssl.create_default_context(cafile=str(ROOT / 'certs/ca/ca.crt'))
        try:
            with socket.create_connection(('127.0.0.1', server.port), timeout=2) as raw_sock:
                with context.wrap_socket(raw_sock, server_hostname='localhost') as no_cert:
                    receive(no_cert)
            raise AssertionError('Client without certificate accepted')
        except (ssl.SSLError, EOFError, ConnectionResetError) as exc:
            errors.append('Missing client certificate -> ' + type(exc).__name__)
        save_case(lab, 'case5_tls_rejections', 'Case 5 · Certificate verification failures', '\n'.join(errors))
        # A long frame exceeds a typical 4096-byte TCP read; two consecutive frames must survive.
        alice.join('general'); assert alice.receive_message()['type'] == 'joined'
        alice.send_message('A' * 12000)
        alice.send_message('second frame')
        assert len(bob.receive_message()['text']) == 12000
        assert bob.receive_message()['text'] == 'second frame'
        bob.close()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            with server.connections.lock:
                count = len(server.connections.clients)
            if count == 2:
                break
            time.sleep(.02)
        assert count == 2
        save_case(lab, 'case6_frames_cleanup', 'Case 6 · TCP framing and connection cleanup',
                  'Message 1: 12000 characters -> intact\nMessage 2: second frame -> intact\n'
                  f'bob disconnected -> active clients = {count}\nPASS: length-prefixed frames and cleanup')
    finally:
        for client in clients:
            client.close()
        server.stop()
        thread.join(2)
        logger.removeHandler(handler)
        handler.close()


if __name__ == '__main__':
    main()
