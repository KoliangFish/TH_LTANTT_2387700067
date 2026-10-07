import json
import click
from modules.runner import run_scan, MODES
from modules.filter_utils import entries
from modules.email_sender import send_email
from modules.report_formatter import format_report


@click.command()
@click.option('--target', default='127.0.0.1', show_default=True)
@click.option('--ports', default='22,80,443', show_default=True)
@click.option('--mode', type=click.Choice(MODES), default='all')
@click.option('--rate-limit', type=click.IntRange(1, 100), default=10)
@click.option('--protocol', type=click.Choice(['tcp', 'udp']), default='tcp')
@click.option('--whitelist', default=None, help='Comma-separated IPv4/CIDR allowlist')
@click.option('--blacklist', default=None, help='Blacklist takes precedence')
@click.option('--nmap', 'use_nmap', is_flag=True, help='Use installed Nmap')
@click.option('--technique', type=click.Choice(['connect', 'syn', 'udp']), default='connect')
@click.option('--email', default=None)
def cli(target, ports, mode, rate_limit, protocol, whitelist, blacklist, use_nmap, technique, email):
    try:
        result = run_scan(target, ports, mode, rate_limit, protocol,
                          entries(whitelist) if whitelist is not None else None,
                          entries(blacklist) if blacklist is not None else None, use_nmap, technique)
        text = json.dumps(result, indent=2, ensure_ascii=False)
        click.echo(text)
        if email:
            click.echo(send_email(email, 'Kết quả quét từ NetRecon', format_report(result)))
    except (ValueError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc


if __name__ == '__main__':
    cli()
