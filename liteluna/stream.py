from litex.soc.interconnect import stream
from migen import *

from liteluna.luna_cores import bulk_streamer
from liteluna.ulpi import ULPIInterface


class USBStreamer(Module):
    def __init__(self, platform, ulpi: ULPIInterface):
        self.platform = platform
        self.ulpi = ulpi

        self.stream_to_host = s2h = stream.Endpoint([("data", 8)])
        self.stream_to_device = s2d = stream.Endpoint([("data", 8)])

        self.specials += Instance(
            "bulk_streamer",
            i_usb_clk=ClockSignal("usb"),
            i_usb_rst=ResetSignal("usb"),
            i_ulpi_data_i=ulpi.data_i,
            o_ulpi_data_o=ulpi.data_o,
            o_ulpi_data_oe=ulpi.data_oe,
            i_ulpi_nxt=ulpi.nxt,
            o_ulpi_stp=ulpi.stp,
            i_ulpi_dir=ulpi.dir,
            o_stream_out_payload=s2d.payload,
        )

    def do_finalize(self):
        verilog_filename = os.path.join(self.platform.output_dir, "gateware", "luna_usbstreamer.v")
        bulk_streamer.USBBulkStreamerDevice.emit_verilog(verilog_filename)
        self.platform.add_source(verilog_filename)
