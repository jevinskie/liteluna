#!/usr/bin/env python3

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(s)
s.connect(("localhost", 2443))


def read():
    sz_buf = s.recv(4)
    sz = int.from_bytes(sz_buf, "big")
    return s.recv(sz)


def write(buf):
    buf = len(buf).to_bytes(4, "big") + buf
    s.send(buf)


while True:
    print(":> ", end="")
    ltx = input()
    write(ltx.encode("utf8"))
    lrx = read().decode("utf8")
    print(f"rx: {lrx}")
