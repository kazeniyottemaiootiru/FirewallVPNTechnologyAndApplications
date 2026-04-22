import socket
import time
import os

# 本机实验版服务端默认只监听回环地址，避免对外暴露端口。
HOST = "192.168.35.141"
# 允许通过环境变量改端口，便于在本机已有占用时切换。
PORT = int(os.environ.get("LAB4_PORT", "8080"))

# 每次从套接字读取的块大小。配合慢速读取，更容易观察 ACK 和窗口。
READ_SIZE = 4096

# 每次读取完之后主动停顿一会儿，放大"接收方处理较慢"的效果，
# 使接收缓冲区更容易被填满，从而在抓包里看到窗口收缩。
READ_DELAY = 0.05

# 请求收完后再延迟返回响应，便于客户端观察 recv() 的阻塞等待。
RESPONSE_DELAY = 2.0


def ts(message: str) -> None:
    # 统一打印带时间戳的日志，方便学生直接记录 connect、recv 等时间点。
    now = time.strftime("%H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def recv_until(conn: socket.socket, marker: bytes) -> bytes:
    # 先读取到 HTTP 风格请求头结束标记，再继续处理正文。
    data = b""
    while marker not in data:
        chunk = conn.recv(1024)
        if not chunk:
            break
        data += chunk
    return data


def main() -> None:
    # 创建 TCP 套接字，后续会经历 bind -> listen -> accept 的典型服务端流程。
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    ts(f"server listening on {HOST}:{PORT}")

    # accept() 返回时，说明三次握手已经完成，服务端拿到了"已建立连接"的套接字。
    conn, addr = server.accept()
    ts(f"accepted from {addr[0]}:{addr[1]}")

    # 把接收缓冲区设置得较小，使接收窗口更容易被慢速读取压缩，
    # 从而在 Wireshark 里更清晰地看到窗口值变化。
    # 注意：Linux 内核会将此值翻倍，实际生效约为这里设置值的 2 倍。
    conn.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32768)

    # 先读到完整请求头，这样可以解析 Content-Length，从而知道后面还要读多少正文。
    initial = recv_until(conn, b"\r\n\r\n")
    header_part, body = initial.split(b"\r\n\r\n", 1)
    headers_text = header_part.decode("ascii", errors="replace")

    # 从请求头中找出 Content-Length，用它来判断正文是否已经全部收齐。
    content_length = 0
    for line in headers_text.split("\r\n"):
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())
            break

    ts(f"request header received, content-length={content_length}")
    ts(f"body already buffered={len(body)} bytes")

    # 故意分块、慢速读取正文。
    # 这样即使客户端一次 sendall() 交出大块数据，
    # 抓包里也更容易看到接收窗口随缓冲区占用而收缩的过程。
    while len(body) < content_length:
        chunk = conn.recv(READ_SIZE)
        if not chunk:
            break
        body += chunk
        ts(f"recv chunk={len(chunk)} bytes, body={len(body)}/{content_length}")
        time.sleep(READ_DELAY)

    ts("request fully received")

    # 故意延迟响应，让客户端的 recv() 有一个明显"等待"的过程，
    # 使客户端输出中的 first recv() returned after ...s 更有说服力。
    ts(f"sleep {RESPONSE_DELAY:.1f}s before sending response")
    time.sleep(RESPONSE_DELAY)

    # 返回一个很小的 HTTP 响应，重点不是 HTTP 本身，而是给 TCP 收发一个清晰的结束点。
    response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Length: 2\r\n"
        b"Connection: close\r\n"
        b"\r\n"
        b"OK"
    )
    conn.sendall(response)
    ts("response sent")

    # 停顿，让抓包中的响应和后续 FIN/ACK 之间有明显间隔，便于区分阶段。
    time.sleep(1.0)

    # 先关已建立连接的套接字，这会触发 FIN，开始四次挥手。
    conn.close()
    ts("connection closed, watching for TIME-WAIT...")

    # 保持进程存活一段时间，让学生有充足的时间在 ss 里观察 TIME-WAIT 状态。
    # TIME-WAIT 在 Linux 上默认持续约 60 秒，这里等 10 秒足够截图。
    time.sleep(10.0)

    server.close()
    ts("server closed")


if __name__ == "__main__":
    main()
