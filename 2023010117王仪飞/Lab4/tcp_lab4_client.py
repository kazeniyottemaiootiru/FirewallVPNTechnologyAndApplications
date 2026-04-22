import socket
import time
import os

# 本机实验版客户端默认连接回环地址上的实验服务端。
HOST = "192.168.35.141"
# 允许通过环境变量改端口，和服务端保持一致即可。
PORT = int(os.environ.get("LAB4_PORT", "8080"))

# 请求体设为 200000 字节（约 200KB）。
# 回环接口的 MSS 通常是 65495，超过这个值才能在抓包中看到 TCP 分段。
BODY_SIZE = 200000


def ts(message: str) -> None:
    # 所有关键步骤都带时间戳输出，方便直接填写实验表格。
    now = time.strftime("%H:%M:%S")
    print(f"[{now}] {message}", flush=True)


def main() -> None:
    # 构造一个带较大正文的 HTTP 风格请求。
    # 这里用 POST 和 Content-Length，是为了让服务端能够持续读取一大段数据。
    body = b"A" * BODY_SIZE
    request = (
        b"POST /lab4 HTTP/1.1\r\n"
        b"Host: 127.0.0.1\r\n"
        + f"Content-Length: {len(body)}\r\n".encode("ascii")
        + b"Connection: close\r\n"
        + b"\r\n"
        + body
    )

    # 创建 TCP 套接字，并关闭 Nagle 算法带来的额外等待，使现象更直接一些。
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    ts("socket created")

    # 停顿，方便在 ss 里观察到"套接字已创建但尚未 connect"的瞬间。
    time.sleep(1.0)

    ts("calling connect()")
    # connect() 返回说明三次握手已经完成，连接进入可收发数据状态。
    client.connect((HOST, PORT))
    ts("connect() returned")

    # 打印本端和对端的地址、端口，便于和 ss、Wireshark 中的连接对应起来。
    local_ip, local_port = client.getsockname()
    peer_ip, peer_port = client.getpeername()
    ts(f"local socket = {local_ip}:{local_port}")
    ts(f"peer socket  = {peer_ip}:{peer_port}")

    # 停顿，让 ESTABLISHED 状态在 ss 里多保持一会儿，便于截图。
    time.sleep(2.0)

    ts(f"sendall() start, request bytes={len(request)}")
    # 应用层只调用一次 sendall()，底层 TCP 是否拆成多个段，正是实验要观察的重点之一。
    client.sendall(request)
    ts("sendall() finished")

    ts("calling recv() and waiting for response")
    # 从进入 recv() 开始计时，用来观察"连接已建立，但应用数据尚未返回"的等待过程。
    start = time.time()
    chunks = []
    total = 0
    while True:
        data = client.recv(4096)
        if not data:
            break
        # 只在第一次读到数据时打印等待时间，突出 recv() 的阻塞效果。
        if not chunks:
            ts(f"first recv() returned after {time.time() - start:.3f}s")
        chunks.append(data)
        total += len(data)
        ts(f"recv chunk={len(data)} bytes, total={total}")

    # 把分块收到的响应重新拼起来，方便直接打印给学生看。
    response = b"".join(chunks)
    ts(f"response bytes={len(response)}")
    print(response.decode("ascii", errors="replace"), flush=True)

    # 停顿，让抓包能清晰区分"响应已收完"和"连接开始断开"两个阶段。
    time.sleep(1.0)

    # 关闭客户端套接字，后续可在抓包中观察关闭过程和 TIME-WAIT。
    client.close()
    ts("client closed")


if __name__ == "__main__":
    main()
