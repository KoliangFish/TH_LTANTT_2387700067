"""Minimal localhost SMTP sink for the lab, not a production mail server."""
import socketserver
import threading
from pathlib import Path

INBOX = Path(__file__).resolve().parent / 'demo-inbox.eml'


class SMTPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b'220 localhost NetRecon demo inbox\r\n')
        data_mode = False
        lines = []
        while line := self.rfile.readline(65536):
            if data_mode:
                if line == b'.\r\n':
                    INBOX.write_bytes(b''.join(lines))
                    self.server.messages.append(b''.join(lines))
                    self.wfile.write(b'250 accepted in local inbox\r\n')
                    data_mode = False
                else:
                    lines.append(line[1:] if line.startswith(b'..') else line)
            elif line.upper().startswith(b'DATA'):
                data_mode = True
                lines = []
                self.wfile.write(b'354 end with dot\r\n')
            elif line.upper().startswith(b'QUIT'):
                self.wfile.write(b'221 bye\r\n')
                return
            elif line.upper().startswith((b'EHLO', b'HELO')):
                self.wfile.write(b'250 localhost\r\n')
            else:
                self.wfile.write(b'250 OK\r\n')


class Inbox(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_inbox(port=1025):
    server = Inbox(('127.0.0.1', port), SMTPHandler)
    server.messages = []
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


if __name__ == '__main__':
    server = start_inbox()
    print('Local SMTP inbox 127.0.0.1:1025; messages saved to demo-inbox.eml')
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
