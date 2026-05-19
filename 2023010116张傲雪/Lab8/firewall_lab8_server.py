#!/usr/bin/env python3
"""
Lab7 服务端脚本

默认监听 0.0.0.0:38070。
通过环境变量修改：
  LAB7_PORT=38170 python3 firewall_lab7_server.py
  LAB7_HOST=192.0.2.2 python3 firewall_lab7_server.py
"""

import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("LAB7_HOST", "0.0.0.0")
PORT = int(os.environ.get("LAB7_PORT", "38070"))


def now():
    return time.strftime("%H:%M:%S")


class Lab7Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        body = (f"lab7 server ok\npath={self.path}\ntime={now()}\n").encode("utf-8")

        # 打印客户端源地址，用来确认请求是否真正到达服务端。
        print(
            f"[{now()}] {self.client_address[0]}:{self.client_address[1]}"
            f" {self.command} {self.path}",
            flush=True,
        )

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), Lab7Handler)
    print(f"lab7 server listening on {HOST}:{PORT}", flush=True)
    print("press Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nserver stopped", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
