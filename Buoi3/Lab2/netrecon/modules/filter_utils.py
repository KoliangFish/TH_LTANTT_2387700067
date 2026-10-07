import ipaddress
import socket
from .audit import LOG


def entries(text):
    return [item.strip() for item in text.split(',') if item.strip()]


def filter_targets(ip_list, whitelist=None, blacklist=None):
    allowed = [ipaddress.ip_network(item, strict=False) for item in (whitelist or [])]
    denied = [ipaddress.ip_network(item, strict=False) for item in (blacklist or [])]
    result = []
    for item in ip_list:
        ip = ipaddress.ip_address(item)
        if any(ip in net for net in denied):
            continue
        if allowed and not any(ip in net for net in allowed):
            continue
        result.append(str(ip))
    return result


def resolve_target(target, whitelist, blacklist):
    if not target or len(target) > 253 or target.startswith('-'):
        raise ValueError('Invalid target')
    try:
        address = str(ipaddress.IPv4Address(target))
    except ipaddress.AddressValueError:
        try:
            address = socket.gethostbyname(target)
        except OSError as exc:
            raise ValueError('Cannot resolve target') from exc
    if not filter_targets([address], whitelist, blacklist):
        LOG.warning('BLOCK target=%s resolved=%s', target, address)
        raise ValueError('Target blocked by whitelist/blacklist')
    LOG.info('ALLOW target=%s resolved=%s', target, address)
    return address


def parse_ports(text):
    ports = set()
    try:
        for token in text.split(','):
            bounds = token.strip().split('-')
            if len(bounds) == 1:
                lo = hi = int(bounds[0])
            elif len(bounds) == 2:
                lo, hi = map(int, bounds)
            else:
                raise ValueError()
            if not 1 <= lo <= hi <= 65535 or hi - lo > 255:
                raise ValueError()
            ports.update(range(lo, hi + 1))
        if not ports or len(ports) > 256:
            raise ValueError()
    except (ValueError, AttributeError):
        raise ValueError('Use ports 1-65535; maximum 256 ports, e.g. 22,80,8000-8003') from None
    return sorted(ports)
