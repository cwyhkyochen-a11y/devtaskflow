from __future__ import annotations

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from dashboard import build_dashboard


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


def run_serve(start: Path | None = None, port: int = 8765, host: str = '127.0.0.1'):
    base = (start or Path.cwd()).resolve()
    result = build_dashboard(base)
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(base), **kwargs)
    server = ThreadingHTTPServer((host, port), handler)
    return server, {
        'url': f'http://{host}:{port}/dtflow-dashboard.html',
        'dashboard_path': result['dashboard_path'],
        'board_path': result['board_path'],
    }
