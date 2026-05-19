#!/usr/bin/env python3
"""
Lab7 客户端脚本

用法:
    python3 firewall_lab7_client.py 192.0.2.2 38070
    LAB7_TIMEOUT=5 python3 firewall_lab7_client.py 192.0.2.2 38070

命令行参数优先于环境变量：
  第一个参数：目标地址（默认 127.0.0.1）
  第二个参数：目标端口（默认 38070）
"""

import os
import socket
import sys
import time


def main():
    if len(sys.argv) >= 2:
        HOST = sys.argv[1]
    else:
        HOST = os.environ.get("LAB7_HOST", "127.0.0.1")

    if len(sys.argv) >= 3:
        PORT = int(sys.argv[2])
    else:
        PORT = int(os.environ.get("LAB7_PORT", "38070"))

    TIMEOUT = float(os.environ.get("LAB7_TIMEOUT", "3"))

    target = (HOST, PORT)
    request = (
        f"GET /lab7?ts={int(time.time())} HTTP/1.1\r\n"
        f"Host: {HOST}:{PORT}\r\n"
        "User-Agent: firewall-lab7-client/1.0\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("ascii")

    print(f"target = http://{HOST}:{PORT}/")
    print(f"timeout = {TIMEOUT:.1f}s")
    print("creating socket")

    start = time.perf_counter()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)

    try:
        print("calling connect()")
        sock.connect(target)
        connected_at = time.perf_counter()
        print(f"connect() returned after {connected_at - start:.3f}s")
        print(f"local socket = {sock.getsockname()[0]}:{sock.getsockname()[1]}")

        print(f"sending HTTP request, bytes={len(request)}")
        sock.sendall(request)

        chunks = []
        while True:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)

        elapsed = time.perf_counter() - start
        response = b"".join(chunks)
        first_line = response.splitlines()[0].decode("iso-8859-1") if response else ""
        print(f"response bytes = {len(response)}")
        print(f"response status = {first_line}")
        print(f"request succeeded after {elapsed:.3f}s")
    except socket.timeout:
        elapsed = time.perf_counter() - start
        print(f"request failed: timeout after {elapsed:.3f}s")
    except OSError as exc:
        elapsed = time.perf_counter() - start
        print(f"request failed: {exc} after {elapsed:.3f}s")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
