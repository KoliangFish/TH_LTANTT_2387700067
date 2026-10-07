import re
import subprocess
from .audit import LOG


class NetworkMapper:
    def map(self):
        try:
            proc = subprocess.run(['arp', '-a'], capture_output=True, text=True,
                                  errors='replace', timeout=5)
            text = proc.stdout
            if proc.returncode:
                raise ValueError('ARP command failed')
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            return {'neighbors': [], 'note': str(exc)}
        neighbors = []
        for line in text.splitlines():
            match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:-]{17})\s+(\S+)', line)
            if match:
                neighbors.append({'ip': match[1], 'mac': match[2], 'type': match[3]})
        LOG.info('MAP ARP neighbors=%s', neighbors)
        return {'neighbors': neighbors, 'note': 'Local ARP cache only; not a complete network topology'}


def map_network():
    return NetworkMapper().map()
