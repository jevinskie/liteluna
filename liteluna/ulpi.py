from migen.genlib.record import Record


class ULPIInterface(Record):
    def __init__(self):
        super().__init__(
            [
                ("clk", 1),
                ("rst", 1),
                ("data_i", 8),
                ("data_o", 8),
                ("data_oe", 8),
                ("nxt", 1),
                ("stp", 1),
                ("dir", 1),
            ]
        )


class ULPIPHYInterface(Record):
    def __init__(self):
        super().__init__(
            [
                ("clk", 1),
                ("rst", 1),
                ("data", 8),
                ("nxt", 1),
                ("stp", 1),
                ("dir", 1),
            ]
        )
