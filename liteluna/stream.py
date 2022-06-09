import os

from litex.soc.interconnect import stream
from migen import *
from migen.genlib.record import DIR_M_TO_S, DIR_S_TO_M, Record

from liteluna.device import USBDeviceLAInterface
from liteluna.luna_cores import bulk_streamer
from liteluna.packet import InterpacketTimerInterface, TokenDetectorInterface
from liteluna.ulpi import ULPIInterface, ULPIPHYInterface
from liteluna.utmi import UTMIInterface


class USBStreamer(Module):
    def __init__(
        self,
        platform,
        pads,
        cd="sys",
        cd_usb="usb",
        cdc_fifo_depth=None,
        with_blinky=False,
        with_utmi_la=False,
        data_clock=None,
    ):
        self.platform = platform
        self.with_utmi = with_utmi = hasattr(pads, "rx_data")
        self.with_blinky = with_blinky
        self.with_utmi_la = with_utmi_la
        self.data_clock = data_clock

        self.inverted_reset = None
        if not set(["rst", "reset"]).isdisjoint(set(dir(pads))):
            self.inverted_reset = False
            try:
                pad_reset = getattr(pads, "rst")
            except AttributeError:
                pad_reset = getattr(pads, "reset")
        elif not set(["rst", "reset"]).isdisjoint(set(dir(pads))):
            self.inverted_reset = True
            try:
                pad_reset = getattr(pads, "rst_n")
            except AttributeError:
                pad_reset = getattr(pads, "reset_n")

        if not with_utmi:
            self.ulpi = ulpi = ULPIInterface()
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
        else:
            self.utmi = utmi = UTMIInterface()
            for name, _, sdir in utmi.layout:
                sname = f"utmi_{name}"
                if sdir == DIR_M_TO_S:
                    self.comb += getattr(utmi, name).eq(getattr(pads, name))
                else:
                    self.comb += getattr(pads, name).eq(getattr(utmi, name))

        self.source_usb = s2h_usb = stream.Endpoint([("data", 8)])
        self.sink_usb = s2d_usb = stream.Endpoint([("data", 8)])
        if cd != cd_usb:
            self.submodules.sink = stream.ClockDomainCrossing(
                self.sink_usb.payload.layout, cd_from=cd_usb, cd_to=cd, depth=cdc_fifo_depth
            )
            self.submodules.sink_pipeline = stream.Pipeline(self.sink_usb, self.sink)
            self.submodules.source = stream.ClockDomainCrossing(
                self.source_usb.payload.layout, cd_from=cd, cd_to=cd_usb, depth=cdc_fifo_depth
            )
            self.submodules.source_pipeline = stream.Pipeline(self.source, self.source_usb)
        else:
            self.sink = self.sink_usb
            self.source = self.source_usb

        self.connect = Signal()

        port_map = {
            "i_usb_clk": ClockSignal(cd_usb),
            "i_usb_rst": ResetSignal(cd_usb),
            "i_connect": self.connect,
            "o_stream_out_payload": s2d_usb.payload.data,
            "o_stream_out_valid": s2d_usb.valid,
            "i_stream_out_ready": s2d_usb.ready,
            "o_stream_out_first": s2d_usb.first,
            "o_stream_out_last": s2d_usb.last,
            "i_stream_in_payload": s2h_usb.payload.data,
            "i_stream_in_valid": s2h_usb.valid,
            "o_stream_in_ready": s2h_usb.ready,
            "i_stream_in_first": s2h_usb.first,
            "i_stream_in_last": s2h_usb.last,
        }

        if not with_utmi:
            ulpi_map = {
                "i_ulpi_data_i": ulpi.data_i,
                "o_ulpi_data_o": ulpi.data_o,
                "o_ulpi_data_oe": ulpi.data_oe,
                "i_ulpi_nxt": ulpi.nxt,
                "o_ulpi_stp": ulpi.stp,
                "i_ulpi_dir": ulpi.dir,
                "o_ulpi_rst": ulpi.rst,
            }
            port_map = dict(port_map, **ulpi_map)
        else:
            utmi_map = {}
            for name, nbit, sdir in utmi.layout:
                sname = f"utmi_{name}"
                sig = getattr(utmi, name)
                if sdir == DIR_M_TO_S:
                    utmi_map[f"i_{sname}"] = sig
                else:
                    utmi_map[f"o_{sname}"] = sig
            port_map = dict(port_map, **utmi_map)
            self.comb += utmi.rx_data.eq(pads.rx_data)

        if with_blinky:
            port_map["o_led"] = platform.request("user_led")

        if with_utmi_la:
            self.utmi_la = UTMIInterface()
            for name, _, _ in self.utmi_la.layout:
                port_map[f"o_utmi_la_{name}"] = getattr(self.utmi_la, name)
            self.utmi_la_rx_data32 = Signal(32)
            self.sync.usb += [
                self.utmi_la_rx_data32[0:8].eq(self.utmi_la.rx_data),
                self.utmi_la_rx_data32[8:16].eq(self.utmi_la_rx_data32[0:8]),
                self.utmi_la_rx_data32[16:24].eq(self.utmi_la_rx_data32[8:16]),
                self.utmi_la_rx_data32[24:32].eq(self.utmi_la_rx_data32[16:24]),
            ]
            self.dev_la = USBDeviceLAInterface()
            for name, _ in self.dev_la.layout:
                port_map[f"o_dev_la_{name}"] = getattr(self.dev_la, name)
            self.td_la = TokenDetectorInterface()
            for name, _, _ in self.td_la.layout:
                port_map[f"o_td_la_{name}"] = getattr(self.td_la, name)
            self.td_la_speed = Signal(2)
            self.td_la_address = Signal(7)
            self.td_la_cnt_dbg = Signal(8)
            self.td_la_state = Signal(8)
            self.td_la_rx_data = Signal(8)
            port_map.update(
                o_td_la_speed=self.td_la_speed,
                o_td_la_address=self.td_la_address,
                o_td_la_cnt_dbg=self.td_la_cnt_dbg,
                o_td_la_state=self.td_la_state,
                o_td_la_rx_data=self.td_la_rx_data,
            )
            self.rxtmr_la = InterpacketTimerInterface()
            for name, _, _ in self.rxtmr_la.layout:
                port_map[f"o_rxtmr_la_{name}"] = getattr(self.rxtmr_la, name)

        self.specials += Instance("bulk_streamer", **port_map)

    def do_finalize(self):
        super().do_finalize()
        verilog_filename = os.path.join(self.platform.output_dir, "gateware", "luna_usbstreamer.v")
        bulk_streamer.USBBulkStreamerDevice.emit_verilog(
            verilog_filename,
            with_utmi=self.with_utmi,
            with_blinky=self.with_blinky,
            with_utmi_la=self.with_utmi_la,
            data_clock=self.data_clock,
        )
        self.platform.add_source(verilog_filename)
