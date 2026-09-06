#!/usr/bin/env python3
"""
Mudlogging Pro — Local HTTP Server & Presentation Launcher
Author: UGM Skripsi
Runs a zero-dependency lightweight web server on http://localhost:8050
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8050
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def find_free_port(start_port=8050):
    import socket
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start_port


def main():
    port = find_free_port(PORT)
    url = f"http://localhost:{port}/index.html"
    
    print("=" * 65)
    print("  MUDLOGGING PRO — 21-Track Multi-Log Petrophysical System")
    print("  UGM Skripsi — Seminar Hasil (Semhas) Release")
    print("=" * 65)
    print(f"  Serving directory: {DIRECTORY}")
    print(f"  Local Web App URL: {url}")
    print("  Press Ctrl+C to terminate the server.")
    print("=" * 65)

    # Launch default web browser
    try:
        webbrowser.open(url)
    except Exception:
        pass

    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.shutdown()


if __name__ == "__main__":
    main()
