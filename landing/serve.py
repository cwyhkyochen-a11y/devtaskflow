#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys

# 使用当前工作目录，不硬编码路径
serve_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)))
os.chdir(serve_dir)
PORT = int(os.environ.get('DTFLOW_LANDING_PORT', 8888))

class Handler(http.server.SimpleHTTPRequestHandler):
    pass

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Serving at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
