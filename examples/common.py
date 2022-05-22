from litex.soc.interconnect import stream
from migen import *


class StreamPayloadInverter(Module):
    def __init__(self):
        self.sink = stream.Endpoint([("data", 8)])
        self.source = stream.Endpoint([("data", 8)])
        self.comb += self.source.connect(self.sink, omit=[self.sink.payload.data])
        inverted_payload = Record([("data", 8)])
        self.comb += inverted_payload.data.eq(~self.sink.payload.data)
