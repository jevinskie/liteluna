from litex.soc.interconnect import stream
from migen import *

from liteluna.luna_cores import bulk_streamer
from liteluna.ulpi import ULPIInterface


class USBStreamer(Module):
    def __init__(self, ulpi: ULPIInterface):
        self.ulpi = ulpi
        self.specials += Instance(
            "bulk_streamer",
            i_clk=ClockSignal("usb"),
            i_rst=ResetSignal("usb"),
            i_ulpi_data_i=ulpi.data_i,
            o_ulpi_data_o=ulpi.data_o,
            o_ulpi_data_oe=ulpi.data_oe,
            i_ulpi_nxt=ulpi.nxt,
            o_ulpi_stp=ulpi.stp,
            i_ulpi_dir=ulpi.dir,
        )
