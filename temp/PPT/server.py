#!/usr/bin/env python3
"""
UGM Skripsi Presentation Deck — Local HTTP Server & Presentation Launcher
Author: Mohammad Azka Khairur Rahman
Runs a lightweight web server on http://localhost:8060
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8060
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def find_free_port(start_port=8060):
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
    print("  UGM SKRIPSI PRESENTATION DECK (HTML SLIDES)")
    print("  Aplikasi Visualisasi Data Gas While Drilling untuk Prediksi Tipe Hidrokarbon")
    print("  Penyusun: Mohammad Azka Khairur Rahman (23/511608/PA/21830)")
    print("=" * 65)
    print(f"  Serving directory: {DIRECTORY}")
    print(f"  Presentation URL : {url}")
    print("  Press Ctrl+C to terminate.")
    print("=" * 65)

    try:
        webbrowser.open(url)
    except Exception:
        pass

    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down presentation server.")
            httpd.shutdown()


if __name__ == "__main__":
    main()
