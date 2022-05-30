#!/usr/bin/env python3

import socket
import time

from usbip_toolkit.usb import *

DEV_ADDR = 0x2B

serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
serv_sock.bind(("localhost", 2443))
serv_sock.listen(1)

s, _ = serv_sock.accept()


def get_odd(reset=False):
    get_odd.odd = getattr(get_odd, "odd", False)
    if reset:
        get_odd.odd = False
    odd = get_odd.odd
    get_odd.odd = not get_odd.odd
    return odd


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

while True:
    sof1_packet = sof_packet(0)
    print(f"sof1_packet: {sof1_packet.hex()}")
    sof2_packet = sof_packet(1)
    print(f"sof2_packet: {sof2_packet.hex()}")

    setup_token = setup_token_packet(0, 0)
    print(f"setup_token: {setup_token.hex()}")

    # setup_buf = bytes.fromhex("8006000100004000")
    setup_buf = bytes.fromhex("00052B0000000000")
    setup_data_packet = data_packet(setup_buf, odd=False)
    print(f"setup_data_packet: {setup_data_packet.hex()}")

    write([sof1_packet, sof2_packet, setup_token, setup_data_packet])

    in_buf = read()
    print(f"in_buf: {in_buf.hex()}")

    sof3_packet = sof_packet(2)

    in_token = in_token_packet(0, 0)
    print(f"in_token: {in_token.hex()}")
    write([sof3_packet, in_token])
    # write(in_token)

    in_buf = read()
    print(f"in_buf: {in_buf.hex()}")

    write(ack_packet())

    # in_buf = read()
    # print(f"in_buf: {in_buf.hex()}")

    input("Press ANY key\n")
