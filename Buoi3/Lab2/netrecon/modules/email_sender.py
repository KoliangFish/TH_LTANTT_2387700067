import os
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv
from .audit import LOG

load_dotenv(Path(__file__).resolve().parents[1] / '.env')


def send_email(receiver_email, subject, body):
    if not receiver_email or '@' not in receiver_email or '\n' in receiver_email or '\r' in receiver_email:
        raise ValueError('Invalid recipient email')
    host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    mode = os.getenv('SMTP_MODE', 'ssl')
    user = os.getenv('SMTP_USER', '')
    password = os.getenv('SMTP_PASS', '')
    port = int(os.getenv('SMTP_PORT', '465'))
    msg = EmailMessage()
    msg['Subject'], msg['From'], msg['To'] = subject, user or 'netrecon@localhost', receiver_email
    msg.set_content(body)
    if mode == 'local':
        if host not in ('localhost', '127.0.0.1'):
            raise ValueError('Local SMTP mode accepts localhost only')
        smtp = smtplib.SMTP(host, port, timeout=5)
    elif mode == 'ssl' and user and password:
        smtp = smtplib.SMTP_SSL(host, port, timeout=10, context=ssl.create_default_context())
    else:
        raise ValueError('Configure SMTP_USER/SMTP_PASS in .env, or use the local demo inbox')
    with smtp:
        if mode != 'local':
            smtp.login(user, password)
        smtp.send_message(msg)
    LOG.info('EMAIL sent recipient=%s host=%s', receiver_email, host)
    return 'Email sent' if mode == 'ssl' else 'Email accepted by local demo inbox (not Gmail)'
