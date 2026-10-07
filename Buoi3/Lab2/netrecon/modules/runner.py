import asyncio
import os
from .audit import LOG
from .filter_utils import entries, resolve_target, parse_ports
from .port_scanner import RateLimiter, async_scan_ports
from .banner_grabber import BannerGrabber
from .service_detector import ServiceDetector, detect_service
from .network_mapper import map_network
from .vuln_checker import check_vulns

MODES = ('scan', 'service', 'banner', 'map', 'vuln', 'all')


def run_scan(target, ports='22,80,443', mode='all', rate_limit=10, protocol='tcp',
             whitelist=None, blacklist=None, use_nmap=False, technique='connect'):
    if mode not in MODES or protocol not in ('tcp', 'udp') or technique not in ('connect', 'syn', 'udp'):
        raise ValueError('Invalid mode/protocol/technique')
    limiter = RateLimiter(rate_limit)
    parsed = parse_ports(ports)
    allowed = entries(os.getenv('NETRECON_WHITELIST', '127.0.0.0/8')) if whitelist is None else whitelist
    denied = entries(os.getenv('NETRECON_BLACKLIST', '')) if blacklist is None else blacklist
    ip = resolve_target(target, allowed, denied)
    LOG.info('START target=%s mode=%s ports=%s rate=%s protocol=%s', ip, mode, parsed, rate_limit, protocol)
    result = {'target': ip, 'mode': mode, 'rate_limit': rate_limit}
    if mode == 'map':
        result['map'] = map_network()
        LOG.info('END target=%s', ip)
        return result
    if technique == 'syn':
        if not use_nmap or protocol != 'tcp' or mode != 'scan':
            raise ValueError('SYN requires --nmap --mode scan --protocol tcp')
        result['scan'] = detect_service(ip, parsed, rate_limit, 'syn', version=False)
        LOG.info('END target=%s', ip)
        return result
    scanned = asyncio.run(async_scan_ports(ip, parsed, rate_limit, protocol, limiter))
    result['scan'] = scanned
    opened = [row['port'] for row in scanned if row['state'] == 'open']
    if protocol == 'tcp' and mode in ('banner', 'service', 'vuln', 'all'):
        grabber = BannerGrabber(limiter)
        banners = {port: grabber.grab(ip, port) for port in opened}
        result['banner'] = banners
        if mode in ('service', 'all'):
            result['service'] = (detect_service(ip, opened, rate_limit) if use_nmap
                                 else ServiceDetector().detect(banners))
        if mode in ('vuln', 'all'):
            result['vuln'] = check_vulns(opened, banners)
    elif protocol == 'udp' and mode in ('service', 'all') and use_nmap:
        result['service'] = detect_service(ip, parsed, rate_limit, 'udp')
    if mode == 'all':
        result['map'] = map_network()
    LOG.info('END target=%s', ip)
    return result
