from enum import IntEnum

from migen import *
from migen.genlib.record import DIR_M_TO_S, DIR_S_TO_M, Record


class LineState(IntEnum):
    SE0 = 0b00
    SQUELCH = 0b00
    FS_HS_K = 0b10
    FS_HS_J = 0b01
    LS_K = 0b01
    LS_J = 0b10


class UTMIInterface(Record):
    def __init__(self):
        super().__init__(
            [
                # Core signals.
                ("rx_data", 8, DIR_M_TO_S),
                ("rx_active", 1, DIR_M_TO_S),
                ("rx_valid", 1, DIR_M_TO_S),
                ("tx_data", 8, DIR_S_TO_M),
                ("tx_valid", 1, DIR_S_TO_M),
                ("tx_ready", 1, DIR_M_TO_S),
                # Control signals.
                ("xcvr_select", 2, DIR_S_TO_M),
                ("term_select", 1, DIR_S_TO_M),
                ("op_mode", 2, DIR_S_TO_M),
                ("suspend", 1, DIR_S_TO_M),
                ("id_pullup", 1, DIR_S_TO_M),
                ("dm_pulldown", 1, DIR_S_TO_M),
                ("dp_pulldown", 1, DIR_S_TO_M),
                ("chrg_vbus", 1, DIR_S_TO_M),
                ("dischrg_vbus", 1, DIR_S_TO_M),
                ("use_external_vbus_indicator", 1, DIR_S_TO_M),
                # Event signals.
                ("line_state", 2, DIR_M_TO_S),
                ("vbus_valid", 1, DIR_M_TO_S),
                ("session_valid", 1, DIR_M_TO_S),
                ("session_end", 1, DIR_M_TO_S),
                ("rx_error", 1, DIR_M_TO_S),
                ("host_disconnect", 1, DIR_M_TO_S),
            ]
        )


class SimUTMIStreamFixup(Module):
    def __init__(self, usb_sim_phy):
        self.utmi = utmi = UTMIInterface()
        self.rx_data_out = rx_data_out = Signal(8)
        self.rx_valid_out = rx_valid_out = Signal()
        self.rx_active_out = rx_active_out = Signal()

        self.hs_activated = hs_activated = Signal()

        self.comb += [
            # source
            utmi.rx_data.eq(rx_data_out),
            utmi.rx_valid.eq(rx_valid_out),
            utmi.rx_active.eq(rx_active_out),
            usb_sim_phy.source.ready.eq(hs_activated),
            # sink
            usb_sim_phy.sink.payload.data.eq(utmi.tx_data),
            usb_sim_phy.sink.valid.eq(utmi.tx_valid & hs_activated),
            utmi.tx_ready.eq(usb_sim_phy.sink.ready),
            # etc
            utmi.vbus_valid.eq(1),
        ]

        self.sync += [
            rx_data_out.eq(usb_sim_phy.source.payload.data),
            rx_valid_out.eq(usb_sim_phy.source.valid),
        ]
        self.comb += rx_active_out.eq(usb_sim_phy.source.valid | rx_valid_out)

        self.reset_fsm = fsm = FSM(reset_state="INIT")
        fsm.act("INIT")
