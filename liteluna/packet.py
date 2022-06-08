from migen.genlib.record import DIR_M_TO_S, DIR_S_TO_M, Record


class TokenDetectorInterface(Record):
    def __init__(self):
        super().__init__(
            [
                ("pid", 4, DIR_S_TO_M),
                ("address", 7, DIR_S_TO_M),
                ("endpoint", 4, DIR_S_TO_M),
                ("new_token", 1, DIR_S_TO_M),
                ("ready_for_response", 1, DIR_S_TO_M),
                ("frame", 11, DIR_S_TO_M),
                ("new_frame", 1, DIR_S_TO_M),
                ("is_in", 1, DIR_S_TO_M),
                ("is_out", 1, DIR_S_TO_M),
                ("is_setup", 1, DIR_S_TO_M),
                ("is_ping", 1, DIR_S_TO_M),
            ]
        )


class InterpacketTimerInterface(Record):
    def __init__(self):
        super().__init__(
            [
                ("start", 1, DIR_M_TO_S),
                ("tx_allowed", 1, DIR_S_TO_M),
                ("tx_timeout", 1, DIR_S_TO_M),
                ("rx_timeout", 1, DIR_S_TO_M),
            ]
        )
