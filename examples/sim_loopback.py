#!/usr/bin/env python3

# Copyright (c) 2022 Jevin Sweval <jevinsweval@gmail.com>
# SPDX-License-Identifier: BSD-2-Clause

import argparse

from common import StreamPayloadInverter
from liteeth.phy.model import LiteEthPHYModel
from litex.build.generic_platform import *
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig
from litex.gen.fhdl.utils import get_signals
from litex.soc.cores.uart import RS232PHYModel
from litex.soc.integration.builder import *
from litex.soc.integration.soc_core import *
from litex.soc.interconnect import stream
from migen import *

# IOs ----------------------------------------------------------------------------------------------

_io = [
    ("sys_clk", 0, Pins(1)),
    ("sys_rst", 0, Pins(1)),
    (
        "serial_udp",
        0,
        Subsignal("source_valid", Pins(1)),
        Subsignal("source_ready", Pins(1)),
        Subsignal("source_data", Pins(8)),
        # Subsignal("source_first", Pins(1)),
        # Subsignal("source_last", Pins(1)),
        Subsignal("sink_valid", Pins(1)),
        Subsignal("sink_ready", Pins(1)),
        Subsignal("sink_data", Pins(8)),
        # Subsignal("sink_first", Pins(1)),
        # Subsignal("sink_last", Pins(1)),
    ),
    (
        "eth_clocks",
        0,
        Subsignal("tx", Pins(1)),
        Subsignal("rx", Pins(1)),
    ),
    (
        "eth",
        0,
        Subsignal("source_valid", Pins(1)),
        Subsignal("source_ready", Pins(1)),
        Subsignal("source_data", Pins(8)),
        Subsignal("sink_valid", Pins(1)),
        Subsignal("sink_ready", Pins(1)),
        Subsignal("sink_data", Pins(8)),
    ),
]


# Platform -----------------------------------------------------------------------------------------


class Platform(SimPlatform):
    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)


# Bench SoC ----------------------------------------------------------------------------------------


class SimSoC(SoCCore):
    def __init__(self, sys_clk_freq=None, **kwargs):
        platform = Platform()
        sys_clk_freq = int(sys_clk_freq)

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(
            self,
            platform,
            clk_freq=sys_clk_freq,
            ident="liteluna bulk loopback simulation",
            **kwargs
        )

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # USB --------------------------------------------------------------------------------------
        self.clock_domains.cd_usb = ClockDomain()
        self.comb += [
            ClockSignal("usb").eq(ClockSignal()),
            ResetSignal("usb").eq(ResetSignal()),
        ]

        serial2udp_pads = self.platform.request("serial_udp")
        self.submodules.usb_sim_phy = usb_sim_phy = RS232PHYModel(serial2udp_pads)

        self.submodules.stream_inverter = StreamPayloadInverter()
        # self.submodules.pipeline = stream.Pipeline(
        #     usb_sim_phy.sink,
        #     # self.stream_inverter,
        #     usb_sim_phy.source,
        #     # usb_sim_phy.source,
        #     # usb_sim_phy.sink,
        # )

        # self.comb += usb_sim_phy.source.connect(usb_sim_phy.sink)
        self.submodules.pipeline = stream.Pipeline(
            usb_sim_phy.source,
            usb_sim_phy.sink,
        )

        # Etherbone --------------------------------------------------------------------------------
        self.submodules.ethphy = LiteEthPHYModel(self.platform.request("eth"))
        self.add_etherbone(phy=self.ethphy, ip_address="192.168.42.50")

        from litescope import LiteScopeAnalyzer

        analyzer_signals = [
            serial2udp_pads,
            *get_signals(usb_sim_phy, recurse=True),
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(
            analyzer_signals, depth=4096, clock_domain="usb", csr_csv="analyzer.csv"
        )


#
# Main ---------------------------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="LiteEth Bench Simulation")
    parser.add_argument("--opt-level", default="O3", help="Verilator optimization level")
    parser.add_argument("--debug-soc-gen", action="store_true", help="Don't run simulation")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    sys_clk_freq = int(20e6)

    sim_config = SimConfig()
    sim_config.add_clocker("sys_clk", freq_hz=sys_clk_freq)
    sim_config.add_module("ethernet", "eth", args={"interface": "tap0", "ip": "192.168.42.100"})
    sim_config.add_module("serial2udp", "serial_udp", args={"port": "2443", "bind_ip": "127.0.0.1"})
    # sim_config.add_module("serial2tcp", "serial_udp", args={"port": "2444"})

    soc_kwargs = soc_core_argdict(args)
    builder_kwargs = builder_argdict(args)

    soc_kwargs["sys_clk_freq"] = sys_clk_freq
    soc_kwargs["cpu_type"] = "None"
    soc_kwargs["uart_name"] = "stub"
    soc_kwargs["ident_version"] = True

    builder_kwargs["csr_csv"] = "csr.csv"

    soc = SimSoC(**soc_kwargs)
    if not args.debug_soc_gen:
        builder = Builder(soc, **builder_kwargs)
        for i in range(2):
            build = i == 0
            run = i == 1
            builder.build(
                build=build,
                run=run,
                sim_config=sim_config,
                opt_level=args.opt_level,
            )


if __name__ == "__main__":
    main()
