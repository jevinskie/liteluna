#!/usr/bin/env python3

# Copyright (c) 2022 Jevin Sweval <jevinsweval@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause


import argparse
import os

from litex.soc.cores.clock import *
from litex.soc.integration.builder import *
from litex.soc.integration.soc_core import *
from litex.soc.interconnect.csr import *
from litex_boards.platforms import terasic_deca
from litex_boards.targets.terasic_deca import _CRG
from migen import *
from migen.genlib.cdc import AsyncResetSynchronizer

from liteluna.stream import USBStreamer
from liteluna.ulpi import ULPIInterface, ULPIPHYInterface

# Bench SoC ----------------------------------------------------------------------------------------


class BenchSoC(SoCCore):
    def __init__(self, with_analyzer=False, sys_clk_freq=int(100e6)):
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
        self.submodules.usb = usb = USBStreamer(platform, ULPIInterface())
        usb.stream_to_host.connect(usb.stream_to_device)

        # scope ------------------------------------------------------------------------------------
        if with_analyzer:
            from litescope import LiteScopeAnalyzer

            analyzer_signals = []
            self.submodules.analyzer = LiteScopeAnalyzer(
                analyzer_signals,
                depth=512,
                clock_domain="sys",
                register=True,
                csr_csv="analyzer.csv",
            )

        # LEDs -------------------------------------------------------------------------------------
        from litex.soc.cores.led import LedChaser

        self.submodules.leds = LedChaser(
            pads=platform.request_all("user_led"), sys_clk_freq=sys_clk_freq
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
