#!/usr/bin/env python3

import socket

serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
serv_sock.bind(("localhost", 2443))
serv_sock.listen(1)

s, _ = serv_sock.accept()


def read():
    sz_buf = s.recv(4)
    sz = int.from_bytes(sz_buf, "big")
    return s.recv(sz)


def write(buf):
    buf = len(buf).to_bytes(4, "big") + buf
    s.send(buf)


while True:
    rxb = read()
    print(f"rx: {rxb.hex()}")
    write(rxb)
