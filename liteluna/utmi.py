from enum import IntEnum

from litex.gen.fhdl.timer import *
from litex.soc.cores.clock.common import ClockFrequency
from migen import *
from migen.genlib.misc import WaitTimer
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
    def __init__(self, usb_sim_phy, cd="sys", cd_usb="usb"):
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

        self.submodules.timer = tmr = MultiWaitTimer(
            {
                "bus_reset": int(ClockFrequency(cd_usb) * 10e-6),
                "chirp": int(ClockFrequency(cd_usb) * 5e-6),
                "toggle": int(ClockFrequency(cd_usb) * 125e-6),
            }
        )
        self.submodules.reset_fsm = fsm = ClockDomainsRenamer(cd_usb)(FSM(reset_state="RESET"))
        fsm.act(
            "RESET",
            Display("RESET"),
            hs_activated.eq(0),
            NextValue(hs_activated, 0),
            tmr.wait.eq(1),
            utmi.line_state.eq(LineState.SE0),
            If(tmr.bus_reset_done, NextState("FS")),
        )
        fsm.act(
            "FS",
            Display("FS"),
            utmi.line_state.eq(LineState.FS_HS_J),
            If(utmi.tx_valid, NextState("GET_CHIRP")),
        )
        self.n_kj = n_kj = Signal(max=3)
        fsm.act(
            "GET_CHIRP",
            Display("GET_CHIRP"),
            utmi.line_state.eq(LineState.FS_HS_J),
            If(~utmi.tx_valid, NextValue(n_kj, 0), NextState("PRE_SEND_K")),
        )
        fsm.act("PRE_SEND_K", tmr.wait.eq(0), NextState("SEND_K"))
        fsm.act(
            "SEND_K",
            tmr.wait.eq(1),
            utmi.line_state.eq(LineState.FS_HS_K),
            If(tmr.chirp_done, NextState("PRE_SEND_J")),
        )
        fsm.act("PRE_SEND_J", tmr.wait.eq(0), NextState("SEND_J"))
        fsm.act(
            "SEND_J",
            tmr.wait.eq(1),
            utmi.line_state.eq(LineState.FS_HS_J),
            If(
                tmr.chirp_done,
                NextValue(n_kj, n_kj + 1),
                If(n_kj == 3, NextState("PRE_HS_ACTIVATED")).Else(NextState("PRE_SEND_K")),
            ),
        )
        fsm.act("PRE_HS_ACTIVATED", tmr.wait.eq(0), NextState("HS_ACTIVATED"))
        fsm.act(
            "HS_ACTIVATED",
            If(1, Display("HS_ACTIVATED IF")),
            Display("HS_ACTIVATED"),
            tmr.wait.eq(1),
            hs_activated.eq(1),
            NextValue(hs_activated, 1),
            utmi.line_state.eq(LineState.FS_HS_J),
            If(tmr.toggle_done, NextState("TOGGLE_K")),
        )
        fsm.act("TOGGLE_K", utmi.line_state.eq(LineState.FS_HS_K), NextState("TOGGLE_J"))
        fsm.act(
            "TOGGLE_J",
            tmr.wait.eq(0),
            utmi.line_state.eq(LineState.FS_HS_J),
            NextState("HS_ACTIVATED"),
        )
