from litex.soc.interconnect import stream
from migen import *


class StreamPayloadInverter(Module):
    def __init__(self):
        self.sink = stream.Endpoint([("data", 8)])
        self.source = stream.Endpoint([("data", 8)])
        self.comb += self.sink.connect(self.source)
        self.comb += self.source.payload.data.eq(~self.sink.payload.data)
