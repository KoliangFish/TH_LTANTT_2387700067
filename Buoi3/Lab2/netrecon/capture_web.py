"""Capture the running web UI with local fixture targets; requires Playwright + Chrome."""
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server
from demo_targets import start_targets
from demo_mail import start_inbox

ROOT = Path(__file__).resolve().parent


def main():
    targets = start_targets(0, 0, 0)
    http, ssh, udp = [server.server_address[1] for server in targets]
    inbox = start_inbox(0)
    os.environ.update(SMTP_HOST='127.0.0.1', SMTP_PORT=str(inbox.server_address[1]), SMTP_MODE='local',
                      SMTP_USER='netrecon@localhost', SMTP_PASS='', NETRECON_WHITELIST='127.0.0.0/8',
                      NETRECON_BLACKLIST='')
    from app import app
    web = make_server('127.0.0.1', 0, app)
    thread = threading.Thread(target=web.serve_forever, daemon=True)
    thread.start()
    images = ROOT.parent / 'images'
    images.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome', headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 960}, device_scale_factor=1)
            page.goto(f'http://127.0.0.1:{web.server_port}')
            page.locator('[name=ports]').fill(f'{http},{ssh}')
            page.locator('[name=email]').fill('student@example.test')
            page.screenshot(path=str(images / 'case7_web_form.png'), full_page=True)
            page.get_by_role('button', name='Scan', exact=True).click()
            page.wait_for_selector('h2:has-text("Kết quả")')
            assert 'accepted by local demo inbox' in page.inner_text('body')
            assert 'NetReconLab/1.0' in page.inner_text('body')
            page.screenshot(path=str(images / 'case8_web_result.png'), full_page=True)
            page.goto(f'http://127.0.0.1:{web.server_port}')
            page.locator('[name=ports]').fill('65536')
            page.get_by_role('button', name='Scan', exact=True).click()
            page.wait_for_selector('[role=alert]')
            page.screenshot(path=str(images / 'case9_web_error.png'), full_page=True)
            page.goto(f'http://127.0.0.1:{web.server_port}')
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            browser.close()
        print('PASS: actual browser form, result, error screenshots; mobile width verified')
    finally:
        web.shutdown(); thread.join(2)
        for server in [*targets, inbox]:
            server.shutdown(); server.server_close()


if __name__ == '__main__':
    main()
