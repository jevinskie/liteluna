from migen.genlib.record import Record


class UTMIInterface(Record):
    def __init__(self):
        super().__init__(
            [
                # Core signals.
                ("rx_data", 8),
                ("rx_active", 1),
                ("rx_valid", 1),
                ("tx_data", 8),
                ("tx_valid", 1),
                ("tx_ready", 1),
                # Control signals.
                ("xcvr_select", 2),
                ("term_select", 1),
                ("op_mode", 2),
                ("suspend", 1),
                ("id_pullup", 1),
                ("dm_pulldown", 1),
                ("dp_pulldown", 1),
                ("chrg_vbus", 1),
                ("dischrg_vbus", 1),
                ("use_external_vbus_indicator", 1),
                # Event signals.
                ("line_state", 2),
                ("vbus_valid", 1),
                ("session_valid", 1),
                ("session_end", 1),
                ("rx_error", 1),
                ("host_disconnect", 1),
                ("id_digital", 1),
            ]
        )
