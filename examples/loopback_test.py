#!/usr/bin/env python3

import random
import time

import usb1

with usb1.USBContext() as context:
    handle = context.openByVendorIDAndProductID(
        0x16D0,
        0xF3B,
        skip_on_error=True,
    )
    assert handle is not None
    with handle.claimInterface(0):
        try:
            while True:
                ibuf = handle.bulkRead(1, 512, timeout=30)
        except:
            pass
        # print("flushed")
        i = 0
        while True:
            obuf = random.randbytes(512)
            # print(f"obuf:     {obuf.hex()}")
            handle.bulkWrite(1, obuf, timeout=1000)
            ibuf = handle.bulkRead(1, 512, timeout=1000)
            # print(f"ibuf:     {ibuf.hex()}")
            # assert ibuf == obuf
            ibuf_inv = bytes([b ^ 0xFF for b in ibuf])
            # print(f"ibuf_inv: {ibuf_inv.hex()}")
            assert ibuf_inv == obuf
            if i % 1024 == 0:
                print(".", end="", flush=True)
            i += 1
