#!/usr/bin/env python3

import socket
import sys

replay_lines = [l.strip() for l in open(sys.argv[1]).readlines()]

serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
serv_sock.bind(("localhost", 2443))
serv_sock.listen(1)

s, _ = serv_sock.accept()


def read():
    sz_buf = s.recv(4)
    sz = int.from_bytes(sz_buf, "big")
    buf = s.recv(sz)
    print(f"d2h_raw: {buf.hex(' ')}", flush=True)
    return buf


def write(bufs):
    if not isinstance(bufs, list):
        bufs = [bufs]
    out_buf = b""
    for buf in bufs:
        out_buf += len(buf).to_bytes(4, "big") + buf
        print(f"h2d_raw: {buf.hex(' ')}", flush=True)
    s.send(out_buf)


for rl in replay_lines:
    if rl.startswith("h2d_raw: "):
        hs = rl.removeprefix("h2d_raw: ")
        obuf = bytes.fromhex(hs)
        print(f"h2d: {obuf.hex(' ')}")
        write(obuf)
    if rl.startswith("d2h_raw: "):
        hs = rl.removeprefix("d2h_raw: ")
        ibuf_gold = bytes.fromhex(hs)
        print(f"ibuf expected: {ibuf_gold.hex(' ')}")
        ibuf = read()
        print(f"ibuf actual:   {ibuf.hex(' ')}")
        if ibuf != ibuf_gold:
            print("MISMATCH")
