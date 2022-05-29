from migen.genlib.record import Record


class USBDeviceLAInterface(Record):
    def __init__(self):
        super().__init__(
            [
                ("connect", 1),
                ("low_speed_only", 1),
                ("full_speed_only", 1),
                ("frame_number", 11),
                ("microframe_number", 3),
                ("sof_detected", 1),
                ("new_frame", 1),
                ("reset_detected", 1),
                ("suspended", 1),
                ("tx_activity_led", 1),
                ("rx_activity_led", 1),
            ]
        )
