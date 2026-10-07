import re
import shutil
import subprocess
from .audit import LOG


class ServiceDetector:
    def detect(self, banners):
        result = {}
        for port, banner in banners.items():
            if banner.startswith('SSH-'):
                service = banner.splitlines()[0]
            elif banner.startswith('HTTP/'):
                match = re.search(r'^Server:\s*(.+)$', banner, re.I | re.M)
                service = 'HTTP / ' + (match.group(1).strip() if match else 'version unknown')
            elif banner.startswith('220'):
                service = 'SMTP/FTP greeting: ' + banner.splitlines()[0]
            else:
                service = 'Unknown; banner insufficient to identify service/version'
            result[port] = service
            LOG.info('SERVICE port=%s result=%r', port, service)
        return result


def detect_service(ip, ports, rate=10, technique='connect', version=True):
    executable = shutil.which('nmap')
    if not executable:
        raise ValueError('Nmap not found in PATH; use built-in banner detection or install Nmap')
    if technique not in ('connect', 'syn', 'udp'):
        raise ValueError('Invalid Nmap technique')
    if not ports:
        return 'No open ports for Nmap service detection'
    flag = {'connect': '-sT', 'syn': '-sS', 'udp': '-sU'}[technique]
    command = [executable, flag, '-Pn', '-n', '--max-rate', str(rate), '--max-retries', '1',
               '--host-timeout', '45s', '-p', ','.join(map(str, ports)), ip]
    if version:
        command.insert(2, '-sV')
        command.insert(3, '--version-light')
    LOG.info('NMAP command=%r', command)
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=50, errors='replace')
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Nmap timed out') from exc
    LOG.info('NMAP exit=%s output=%r', proc.returncode, proc.stdout)
    if proc.returncode:
        raise ValueError('Nmap failed: ' + proc.stderr[:400])
    return proc.stdout
