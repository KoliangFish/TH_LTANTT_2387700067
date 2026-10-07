from .audit import LOG


class VulnChecker:
    """Evidence-based configuration indicators, never infer a CVE from a port number."""
    def check(self, open_ports, banners):
        findings = []
        for port in open_ports:
            banner = banners.get(port, '')
            if port in (21, 23) or banner.startswith('220'):
                findings.append({'port': port, 'level': 'review',
                                 'finding': 'Possible plaintext protocol; verify TLS/configuration'})
            if banner.startswith('HTTP/'):
                findings.append({'port': port, 'level': 'review',
                                 'finding': 'HTTP plaintext observed; use HTTPS for sensitive data'})
                if 'Server:' in banner:
                    findings.append({'port': port, 'level': 'info',
                                     'finding': 'Server software banner disclosed'})
        LOG.info('VULN indicators=%r; CVE status unconfirmed', findings)
        return {'findings': findings, 'note': 'Indicators only. CVE requires product, version and configuration evidence.'}


def check_vulns(ports, banners=None):
    return VulnChecker().check(ports, banners or {})
