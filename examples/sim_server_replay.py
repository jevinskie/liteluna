#!/usr/bin/env python3

import socket
import sys
import time

replay_lines = [l.strip() for l in open(sys.argv[1]).readlines()]

serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
serv_sock.bind(("localhost", 2443))
serv_sock.listen(1)

s, _ = serv_sock.accept()
s.settimeout(10)


def read():
    sz_buf = s.recv(4)
    sz = int.from_bytes(sz_buf, "big")
    buf = s.recv(sz)
    # print(f"d2h_raw: {buf.hex(' ')}", flush=True)
    return buf


def write(bufs):
    if not isinstance(bufs, list):
        bufs = [bufs]
    out_buf = b""
    for buf in bufs:
        smsg = len(buf).to_bytes(4, "big") + buf
        out_buf += smsg
        time.sleep(0.001)
        s.send(smsg)
        # print(f"h2d_raw: {buf.hex(' ')}", flush=True)
    # s.send(out_buf)


for rl in replay_lines:
    if rl.startswith("#"):
        print(rl)
    if rl.startswith("h2d_raw: ") or rl.startswith("h2d: "):
        hs = rl.removeprefix("h2d_raw: ")
        hs = hs.removeprefix("h2d: ")
        obuf = bytes.fromhex(hs)
        print(f"h2d: {obuf.hex(' ')}")
        write(obuf)
    if rl.startswith("d2h_raw: ") or rl.startswith("d2h: "):
        hs = rl.removeprefix("d2h_raw: ")
        hs = hs.removeprefix("d2h: ")
        ibuf_gold = bytes.fromhex(hs)
        print(f"ibuf expected: {ibuf_gold.hex(' ')}")
        ibuf = read()
        print(f"ibuf actual:   {ibuf.hex(' ')}")
        if ibuf != ibuf_gold:
            print("MISMATCH")

s.settimeout(1)
i = 0
while True:
    try:
        ibuf = read()
        print(f"extra ibuf {i}: {ibuf.hex(' ')}")
        i += 1
    except TimeoutError:
        print("no more leftovers")
        break
