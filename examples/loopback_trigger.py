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
        handle.bulkWrite(1, b"\xaa\x55\x00\xff", timeout=1000)
        ibuf = handle.bulkRead(1, 4, timeout=1000)
        print(ibuf.hex())
