import asyncio
import socket
import threading
import time
from .audit import LOG


class RateLimiter:
    """Space probe starts across TCP, UDP, banner and service operations."""
    def __init__(self, rate=10):
        if not 1 <= rate <= 100:
            raise ValueError('Rate limit must be 1-100 probes/second')
        self.interval = 1 / rate
        self.next_start = 0.0
        self.lock = threading.Lock()

    def wait(self):
        with self.lock:
            delay = self.next_start - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            self.next_start = time.monotonic() + self.interval


class PortScanner:
    def __init__(self, limiter, timeout=3):
        self.limiter = limiter
        self.timeout = timeout

    def scan(self, target, port, protocol='tcp'):
        self.limiter.wait()
        kind = socket.SOCK_STREAM if protocol == 'tcp' else socket.SOCK_DGRAM
        with socket.socket(socket.AF_INET, kind) as sock:
            sock.settimeout(self.timeout)
            try:
                sock.connect((target, port))
                if protocol == 'udp':
                    sock.send(b'NetRecon lab probe')
                    sock.recv(1024)
                state = 'open'
            except (ConnectionRefusedError, ConnectionResetError):
                state = 'closed'
            except (socket.timeout, TimeoutError):
                state = 'filtered' if protocol == 'tcp' else 'open|filtered'
            except OSError:
                state = 'unreachable'
        LOG.info('PROBE target=%s port=%s protocol=%s state=%s', target, port, protocol, state)
        return {'port': port, 'protocol': protocol, 'state': state}


async def async_scan_ports(target, ports, rate_limit=10, protocol='tcp', limiter=None):
    scanner = PortScanner(limiter or RateLimiter(rate_limit))
    # Sequential dispatch deliberately keeps the configured temporal rate predictable.
    return [await asyncio.to_thread(scanner.scan, target, port, protocol) for port in ports]
