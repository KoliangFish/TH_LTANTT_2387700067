import socket
from .audit import LOG


class BannerGrabber:
    def __init__(self, limiter):
        self.limiter = limiter

    def grab(self, target, port):
        self.limiter.wait()
        try:
            with socket.create_connection((target, port), timeout=1) as sock:
                sock.settimeout(.4)
                try:
                    banner = sock.recv(2048)
                except socket.timeout:
                    sock.sendall(f'HEAD / HTTP/1.0\r\nHost: {target}\r\n\r\n'.encode())
                    banner = sock.recv(2048)
            result = banner.decode('utf-8', errors='replace').strip()
        except OSError as exc:
            result = f'No readable banner: {type(exc).__name__}'
        LOG.info('BANNER target=%s port=%s result=%r', target, port, result[:2048])
        return result


def grab_banner(ip, port, limiter):
    return BannerGrabber(limiter).grab(ip, port)
