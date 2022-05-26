from migen.genlib.record import DIR_M_TO_S, DIR_S_TO_M, Record


class UTMIInterface(Record):
    def __init__(self):
        super().__init__(
            [
                # Core signals.
                ("rx_data", 8, DIR_S_TO_M),
                ("rx_active", 1, DIR_S_TO_M),
                ("rx_valid", 1, DIR_S_TO_M),
                ("tx_data", 8, DIR_M_TO_S),
                ("tx_valid", 1, DIR_M_TO_S),
                ("tx_ready", 1, DIR_S_TO_M),
                # Control signals.
                ("xcvr_select", 2, DIR_M_TO_S),
                ("term_select", 1, DIR_M_TO_S),
                ("op_mode", 2, DIR_M_TO_S),
                ("suspend", 1, DIR_M_TO_S),
                ("id_pullup", 1, DIR_M_TO_S),
                ("dm_pulldown", 1, DIR_M_TO_S),
                ("dp_pulldown", 1, DIR_M_TO_S),
                ("chrg_vbus", 1, DIR_M_TO_S),
                ("dischrg_vbus", 1, DIR_M_TO_S),
                ("use_external_vbus_indicator", 1, DIR_M_TO_S),
                # Event signals.
                ("line_state", 2, DIR_S_TO_M),
                ("vbus_valid", 1, DIR_S_TO_M),
                ("session_valid", 1, DIR_S_TO_M),
                ("session_end", 1, DIR_S_TO_M),
                ("rx_error", 1, DIR_S_TO_M),
                ("host_disconnect", 1, DIR_S_TO_M),
                ("id_digital", 1, DIR_S_TO_M),
            ]
        )
