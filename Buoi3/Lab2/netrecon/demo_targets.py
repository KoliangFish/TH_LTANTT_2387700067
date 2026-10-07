"""Local reproducible HTTP, SSH-like banner and UDP echo targets."""
import socketserver
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HTTP(BaseHTTPRequestHandler):
    server_version = 'NetReconLab/1.0'
    sys_version = ''

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.do_HEAD()
        self.wfile.write(b'NetRecon local lab target')

    def log_message(self, *args):
        pass


class SSH(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.sendall(b'SSH-2.0-NetReconLab_1.0\r\n')


class UDP(socketserver.BaseRequestHandler):
    def handle(self):
        data, sock = self.request
        sock.sendto(b'NetRecon echo: ' + data, self.client_address)


class TCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_targets(http_port=8000, ssh_port=8022, udp_port=8053):
    servers = [ThreadingHTTPServer(('127.0.0.1', http_port), HTTP),
               TCPServer(('127.0.0.1', ssh_port), SSH),
               socketserver.ThreadingUDPServer(('127.0.0.1', udp_port), UDP)]
    for server in servers:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    return servers


if __name__ == '__main__':
    servers = start_targets()
    print('Local targets: HTTP TCP 8000, SSH-like TCP 8022, UDP echo 8053; Ctrl+C to stop')
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()
