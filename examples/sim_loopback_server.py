#!/usr/bin/env python3

import socket
import time

from usbip_toolkit.usb import *

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


def write(bufs):
    if not isinstance(bufs, list):
        bufs = [bufs]
    out_buf = b""
    for buf in bufs:
        out_buf += len(buf).to_bytes(4, "big") + buf
    s.send(out_buf)


# while True:
#     rxb = read()
#     print(f"rx: {rxb.hex()}")
#     write(rxb)

# time.sleep(7)

input("Press ANY key\n")

odd = False

while True:
    sof1_packet = sof_packet(0)
    print(f"sof1_packet: {sof1_packet.hex()}")
    sof2_packet = sof_packet(1)
    print(f"sof2_packet: {sof2_packet.hex()}")

    setup_token_packet = setup_packet(0, 0)
    print(f"setup_token_packet: {setup_token_packet.hex()}")

    setup_buf = bytes.fromhex("8006000100004000")
    setup_data_packet, odd = data_packet(setup_buf, odd=odd)
    print(f"setup_data_packet: {setup_data_packet.hex()}")

    write([sof1_packet, sof2_packet, setup_token_packet, setup_data_packet])

    in_buf = read()
    print(f"in_buf: {in_buf.hex()}")

    sof3_packet = sof_packet(2)

    in_token_packet = in_packet(0, 0)
    print(f"in_token_packet: {in_token_packet.hex()}")
    write([sof3_packet, in_token_packet])

    in_buf = read()
    print(f"in_buf: {in_buf.hex()}")

    input("Press ANY key\n")
