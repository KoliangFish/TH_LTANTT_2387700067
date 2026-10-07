"""Integration cases with local targets, real CLI, web routes and SMTP sink."""
import json
import os
import subprocess
import sys
import time
from email import policy
from email.parser import BytesParser
from pathlib import Path
from demo_targets import start_targets
from demo_mail import start_inbox
from modules.runner import run_scan
from modules.port_scanner import RateLimiter
from modules.filter_utils import parse_ports

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1]))
from evidence import save_case


def main():
    # Ephemeral fixture ports avoid interfering with the user's services.
    targets = start_targets(0, 0, 0)
    http, ssh, udp = [server.server_address[1] for server in targets]
    inbox = start_inbox(0)
    os.environ.update(SMTP_HOST='127.0.0.1', SMTP_PORT=str(inbox.server_address[1]), SMTP_MODE='local',
                      SMTP_USER='netrecon@localhost', SMTP_PASS='', NETRECON_WHITELIST='127.0.0.0/8',
                      NETRECON_BLACKLIST='')
    import socket
    with socket.socket() as closed_socket:
        closed_socket.bind(('127.0.0.1', 0))
        closed = closed_socket.getsockname()[1]
    lab = ROOT.parent
    try:
        command = [sys.executable, str(ROOT / 'cli.py'), '--target', '127.0.0.1', '--ports',
                   f'{http},{ssh},{closed}', '--mode', 'scan', '--rate-limit', '10']
        proc = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                              env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}, timeout=15)
        assert proc.returncode == 0, proc.stderr
        rows = json.loads(proc.stdout)['scan']
        assert {row['port']: row['state'] for row in rows} == {http: 'open', ssh: 'open', closed: 'closed'}
        save_case(lab, 'case1_tcp_cli', 'Case 1 · Real CLI TCP open/closed scan',
                  f'python cli.py --target 127.0.0.1 --ports {http},{ssh},{closed} --mode scan\n' + proc.stdout)
        result = run_scan('127.0.0.1', str(udp), 'scan', protocol='udp')
        assert result['scan'][0]['state'] == 'open'
        save_case(lab, 'case2_udp', 'Case 2 · UDP response proves open port', json.dumps(result, indent=2))
        result = run_scan('127.0.0.1', f'{http},{ssh},{closed}', 'all')
        assert 'NetReconLab/1.0' in result['service'][http]
        assert result['service'][ssh].startswith('SSH-2.0')
        assert result['vuln']['findings']
        displayed = {**result, 'map': {'neighbors': result['map']['neighbors'][:3],
                                     'note': result['map']['note'],
                                     'total_neighbors': len(result['map']['neighbors']),
                                     'display': 'First 3 ARP entries shown; remaining entries omitted'}}
        save_case(lab, 'case3_services', 'Case 3 · Banner, service, ARP map, configuration review',
                  json.dumps(displayed, ensure_ascii=False, indent=2))
        failures = []
        for kwargs in ({'blacklist': ['127.0.0.1']}, {'whitelist': ['192.0.2.0/24']}):
            try:
                run_scan('127.0.0.1', str(http), 'scan', **kwargs)
                raise AssertionError('Policy bypass')
            except ValueError as exc:
                failures.append(str(kwargs) + ' -> ' + str(exc))
        for ports in ('0', '65536', '80;whoami', '1-65535'):
            try:
                parse_ports(ports)
                raise AssertionError('Invalid ports accepted')
            except ValueError:
                failures.append(f'ports={ports!r} -> rejected')
        limiter = RateLimiter(5)
        starts = []
        for _ in range(4):
            limiter.wait(); starts.append(time.monotonic())
        elapsed = starts[-1] - starts[0]
        assert elapsed >= .59
        failures.append(f'4 probe slots at 5/second: elapsed {elapsed:.3f}s (expected >=0.6s)')
        save_case(lab, 'case4_policy_rate', 'Case 4 · Policy, validation and temporal rate limit', '\n'.join(failures))
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as web:
            assert web.get('/').status_code == 200
            response = web.post('/scan', data={'target': '127.0.0.1', 'ports': f'{http},{ssh},{closed}',
                                               'mode': 'all', 'email': 'student@example.test'})
            assert response.status_code == 200
            assert b'accepted by local demo inbox' in response.data
            invalid = web.post('/scan', data={'target': '127.0.0.1', 'ports': '65536'})
            assert invalid.status_code == 400
        assert inbox.messages
        mail = BytesParser(policy=policy.default).parsebytes(inbox.messages[-1])
        assert mail['To'] == 'student@example.test'
        assert 'scan' in mail.get_body().get_content()
        save_case(lab, 'case5_web_email', 'Case 5 · Flask routes and real local SMTP delivery',
                  'GET / -> HTTP 200\nPOST /scan (all + email) -> HTTP 200\nPOST /scan invalid ports -> HTTP 400\n'
                  f'SMTP inbox: 127.0.0.1:{inbox.server_address[1]}\nTo: {mail["To"]}\nSubject: {mail["Subject"]}\n'
                  'SMTP DATA accepted and parsed successfully\nLocal inbox only; no message sent to Gmail\n'
                  f'Email body size: {len(mail.get_body().get_content())} characters\n'
                  'First 30 lines of received email body:\n\n' + '\n'.join(mail.get_body().get_content().splitlines()[:30]))
        log = (ROOT / 'netrecon.log').read_text(encoding='utf-8').splitlines()
        lines = [line if len(line) <= 180 else line[:180] + ' ... [line truncated for image]' for line in log[-18:]]
        save_case(lab, 'case6_audit', 'Case 6 · Timestamped activity audit', '\n'.join(lines))
        print('All NetRecon integration cases passed')
    finally:
        for server in [*targets, inbox]:
            server.shutdown(); server.server_close()


if __name__ == '__main__':
    main()
