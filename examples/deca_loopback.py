#!/usr/bin/env python3

# Copyright (c) 2022 Jevin Sweval <jevinsweval@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause


import argparse
import os

from common import StreamPayloadInverter
from litex.gen.fhdl.utils import get_signals
from litex.soc.cores.clock import *
from litex.soc.cores.led import LedChaser
from litex.soc.integration.builder import *
from litex.soc.integration.soc_core import *
from litex.soc.interconnect import stream
from litex.soc.interconnect.csr import *
from litex_boards.platforms import terasic_deca
from litex_boards.targets.terasic_deca import _CRG
from migen import *
from migen.genlib.cdc import AsyncResetSynchronizer

from liteluna.stream import USBStreamer
from liteluna.ulpi import ULPIInterface, ULPIPHYInterface

# Bench SoC ----------------------------------------------------------------------------------------


class BenchSoC(SoCCore):
    def __init__(self, with_analyzer=False, sys_clk_freq=int(125e6)):
        platform = terasic_deca.Platform()

        self.ulpi = platform.request("ulpi")

        # SoCMini ----------------------------------------------------------------------------------
        SoCMini.__init__(
            self,
            platform,
            clk_freq=sys_clk_freq,
            ident="LiteLUNA looopback example on on MAX10 DECA",
            ident_version=True,
        )

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq, with_usb_pll=True, ulpi=self.ulpi)

        # JTAGbone ---------------------------------------------------------------------------------
        self.add_jtagbone()

        # USBbone ----------------------------------------------------------------------------------
        self.submodules.usb = usb = USBStreamer(platform, self.ulpi, with_blinky=True)
        # self.comb += self.ulpi.reset_n.eq(
        #     ~(ResetSignal("sys") | (~self.ulpi.reset_n & self.crg.usb_pll.locked))
        # )
        self.comb += self.ulpi.reset_n.eq(1)
        self.submodules.stream_inverter = StreamPayloadInverter()
        # self.submodules.pipeline = stream.Pipeline(
        #     usb.stream_to_device,
        #     self.stream_inverter,
        #     usb.stream_to_host,
        # )

        self.comb += self.stream_inverter.sink.connect(usb.stream_to_host)
        self.comb += usb.stream_to_device.connect(self.stream_inverter.source)

        # self.comb += usb.stream_to_device.connect(usb.stream_to_host)
        self.comb += usb.connect.eq(1)

        led_usb = LedChaser(pads=platform.request("user_led"), sys_clk_freq=60e6)
        self.submodules.led_usb = ClockDomainsRenamer("usb")(led_usb)
        # self.submodules.led_usb = led_usb

        # 1 led padding between USB blinky and LiteX chaser
        self.comb += platform.request("user_led").eq(1)

        # scope ------------------------------------------------------------------------------------
        if with_analyzer:
            from litescope import LiteScopeAnalyzer

            usb_clk_cnt = Signal(4)
            self.sync.usb += usb_clk_cnt.eq(usb_clk_cnt + 1)
            usb_rst = Signal()
            self.comb += [
                usb_rst.eq(ResetSignal("usb")),
            ]

            ulpi_sigs = get_signals(self.ulpi)
            ulpi_sigs.remove(self.ulpi.clk)

            analyzer_signals = [
                *ulpi_sigs,
                *get_signals(usb, recurse=False),
                *get_signals(self.stream_inverter),
                # *get_signals(usb.stream_to_host),
                # *get_signals(usb.stream_to_device),
                usb_clk_cnt,
                usb_rst,
                self.crg.usb_pll.locked,
            ]
            self.submodules.analyzer = LiteScopeAnalyzer(
                analyzer_signals,
                depth=512,
                clock_domain="sys",
                register=True,
                csr_csv="analyzer.csv",
            )

        # LEDs -------------------------------------------------------------------------------------
        self.submodules.leds = LedChaser(
            pads=platform.request_remaining("user_led"), sys_clk_freq=sys_clk_freq
        )


# Main ---------------------------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="LiteLUNA looopback example on on MAX10 DECA")
    parser.add_argument("--build", action="store_true", help="Build bitstream")
    parser.add_argument("--load", action="store_true", help="Load bitstream")
    parser.add_argument("--with-analyzer", action="store_true", help="Enable litescope")
    args = parser.parse_args()

    soc = BenchSoC(with_analyzer=args.with_analyzer)
    builder = Builder(soc, csr_csv="csr.csv")
    builder.build(run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".sof"))


if __name__ == "__main__":
    main()
