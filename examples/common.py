from litex.soc.interconnect import stream
from migen import *


class StreamPayloadInverter(Module):
    def __init__(self):
        self.sink = stream.Endpoint([("data", 8)])
        self.source = stream.Endpoint([("data", 8)])
        print(f"self.source.layout: {self.source.layout}")
        self.comb += self.source.connect(self.sink, omit=["data"])
        inverted_payload = Signal(8)
        self.comb += inverted_payload.eq(~self.sink.payload.data)
        self.comb += self.source.payload.data.eq(inverted_payload)
