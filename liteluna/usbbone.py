from typing import Union

from litex.soc.cores import uart
from litex.soc.cores.clock.common import ClockFrequency
from migen import *

from liteluna.stream import USBStreamer
from liteluna.ulpi import ULPIInterface
from liteluna.utmi import UTMIInterface


def add_usbbone(
    soc,
    usb: Union[USBStreamer, ULPIInterface, UTMIInterface],
    name="usbbone",
    usb_cd="usb",
    buffer_depth=16,
    with_blinky=False,
):
    soc.check_if_exists(name)
    if type(usb) in (ULPIInterface, UTMIInterface):
        usb_pads = usb
        usb = USBStreamer(soc.platform, usb_pads, with_blinky=with_blinky)
    usbbone = uart.UARTBone(phy=usb, clk_freq=ClockFrequency(usb_cd), cd=usb_cd)
    setattr(soc.submodules, f"{name}_phy", usb)
    setattr(soc.submodules, name, usbbone)
    soc.bus.add_master(name=name, master=usbbone.wishbone)


class LiteLUNAUSBbonePacket(Module):
    def __init__(self, usb):
        self.submodules.tx = tx = LiteLUNAUSBbonePacketTX()
        self.submodules.rx = rx = LiteLUNAUSBbonePacketRX()
        udp_port = udp.crossbar.get_port(udp_port, dw=32, cd=cd)
        self.comb += [tx.source.connect(udp_port.sink), udp_port.source.connect(rx.sink)]
        self.sink, self.source = self.tx.sink, self.rx.source


# USBbone -----------------------------------------------------------------------------------------


class LiteLUNAUSBbone(Module):
    def __init__(self, buffer_depth=4, cd="sys"):
        # Encode/encode etherbone packets
        self.submodules.packet = packet = LiteLUNAUSBbonePacket(cd)

        self.submodules.record = record = LiteLUNAUSBboneRecord(buffer_depth=buffer_depth)

        # Arbitrate/dispatch probe/records packets
        dispatcher = Dispatcher(packet.source, [probe.sink, record.sink])
        self.comb += dispatcher.sel.eq(~packet.source.pf)
        arbiter = Arbiter([probe.source, record.source], packet.sink)
        self.submodules += dispatcher, arbiter

        # Create MMAP wishbone
        self.submodules.wishbone = LiteLUNAUSBboneWishboneMaster()
        self.comb += [
            record.receiver.source.connect(self.wishbone.sink),
            self.wishbone.source.connect(record.sender.sink),
        ]
