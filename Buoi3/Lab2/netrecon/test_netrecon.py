import pytest
from modules.filter_utils import parse_ports, filter_targets
from modules.vuln_checker import check_vulns
from modules.service_detector import ServiceDetector
from modules.runner import run_scan


def test_range_and_deduplication():
    assert parse_ports('80,8000-8002,80') == [80, 8000, 8001, 8002]


@pytest.mark.parametrize('text', ['0', '65536', '2-1', '80;echo', '', '1-65535'])
def test_bad_ports_rejected(text):
    with pytest.raises(ValueError):
        parse_ports(text)


def test_blacklist_precedence():
    assert filter_targets(['127.0.0.1', '127.0.0.2'], ['127.0.0.0/8'], ['127.0.0.1']) == ['127.0.0.2']


def test_no_cve_claim_from_open_port():
    assert check_vulns([80, 443, 22])['findings'] == []


def test_service_evidence():
    result = ServiceDetector().detect({8000: 'HTTP/1.0 200 OK\r\nServer: Lab/1.0\r\n', 8022: 'SSH-2.0-Lab'})
    assert result == {8000: 'HTTP / Lab/1.0', 8022: 'SSH-2.0-Lab'}


def test_syn_cannot_silently_fall_back():
    with pytest.raises(ValueError, match='SYN requires'):
        run_scan('127.0.0.1', '80', 'scan', technique='syn', use_nmap=False)
