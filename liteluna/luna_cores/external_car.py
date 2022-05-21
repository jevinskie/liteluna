# This file is derived from LUNA.
#
# Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
# Copyright (c) 2022 Jevin Sweval <jevinsweval@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from amaranth import *


class ExternalClockAndResetController(Elaboratable):
    """Controller for external clocking and global resets."""

    def __init__(self):
        self.usb_clk = Signal()
        self.usb_rst = Signal()

    def elaborate(self, platform):
        m = Module()

        # Create our domains; but don't do anything else for them, for now.
        # m.domains.sync   = ClockDomain()
        m.domains.usb = ClockDomain()

        m.d.comb += [
            ClockSignal("usb").eq(self.usb_clk),
            ResetSignal("usb").eq(self.usb_rst),
        ]

        return m
