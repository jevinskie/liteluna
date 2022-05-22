import os

from litex.soc.interconnect import stream
from migen import *

from liteluna.luna_cores import bulk_streamer
from liteluna.ulpi import ULPIInterface, ULPIPHYInterface


class USBStreamer(Module):
    def __init__(self, platform, pads, with_blinky=False):
        self.platform = platform
        self.ulpi = ulpi = ULPIInterface()
        self.with_blinky = with_blinky

        self.inverted_reset = False
        if not set(["rst", "reset"]).isdisjoint(set(dir(pads))):
            try:
                pad_reset = getattr(pads, "rst")
            except AttributeError:
                pad_reset = getattr(pads, "reset")
        else:
            self.inverted_reset = True
            try:
                pad_reset = getattr(pads, "rst_n")
            except AttributeError:
                pad_reset = getattr(pads, "reset_n")

        # if not self.inverted_reset:
        #     self.comb += pad_reset.eq(ulpi.rst)
        # else:
        #     self.comb += pad_reset.eq(~ulpi.rst)

        data_ts = TSTriple(8)
        self.specials += data_ts.get_tristate(pads.data)

        self.comb += [
            ulpi.data_i.eq(data_ts.i),
            data_ts.o.eq(ulpi.data_o),
            data_ts.oe.eq(ulpi.data_oe),
            ulpi.nxt.eq(pads.nxt),
            pads.stp.eq(ulpi.stp),
            ulpi.dir.eq(pads.dir),
        ]

        self.stream_to_host = s2h = stream.Endpoint([("data", 8)])
        self.stream_to_device = s2d = stream.Endpoint([("data", 8)])

        self.connect = Signal()

        port_map = {
            "i_usb_clk": ClockSignal("usb"),
            "i_usb_rst": ResetSignal("usb"),
            "i_ulpi_data_i": ulpi.data_i,
            "o_ulpi_data_o": ulpi.data_o,
            "o_ulpi_data_oe": ulpi.data_oe,
            "i_ulpi_nxt": ulpi.nxt,
            "o_ulpi_stp": ulpi.stp,
            "i_ulpi_dir": ulpi.dir,
            "o_ulpi_rst": ulpi.rst,
            "i_connect": self.connect,  # breaks clocking???
            "o_stream_out_payload": s2d.payload.data,
            "o_stream_out_valid": s2d.valid,
            "i_stream_out_ready": s2d.ready,
            "o_stream_out_first": s2d.first,
            "o_stream_out_last": s2d.last,
            "i_stream_in_payload": s2h.payload.data,
            "i_stream_in_valid": s2h.valid,
            "o_stream_in_ready": s2h.ready,
            "i_stream_in_first": s2h.first,
            "i_stream_in_last": s2h.last,
        }
        if with_blinky:
            port_map["o_led"] = platform.request("user_led")

        self.specials += Instance("bulk_streamer", **port_map)

    def do_finalize(self):
        super().do_finalize()
        verilog_filename = os.path.join(self.platform.output_dir, "gateware", "luna_usbstreamer.v")
        bulk_streamer.USBBulkStreamerDevice.emit_verilog(
            verilog_filename, with_blinky=self.with_blinky
        )
        self.platform.add_source(verilog_filename)
