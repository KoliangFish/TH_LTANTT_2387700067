import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request
from modules.runner import run_scan
from modules.email_sender import send_email
from modules.report_formatter import format_report

load_dotenv(Path(__file__).resolve().parent / '.env')
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16384


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/scan')
def scan():
    try:
        result = run_scan(request.form.get('target', ''), request.form.get('ports', ''),
                          request.form.get('mode', 'all'), int(request.form.get('rate_limit', '10')),
                          request.form.get('protocol', 'tcp'),
                          use_nmap=request.form.get('nmap') == 'on',
                          technique=request.form.get('technique', 'connect'))
    except (ValueError, OSError) as exc:
        return render_template('index.html', error=str(exc)), 400
    email_status = 'Không yêu cầu gửi email'
    email = request.form.get('email', '').strip()
    if email:
        try:
            email_status = send_email(email, 'Kết quả quét từ NetRecon', format_report(result))
        except (ValueError, OSError) as exc:
            email_status = 'Email thất bại: ' + str(exc)
    return render_template('result.html', result=result, email_status=email_status)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('NETRECON_PORT', '5000')))
