from litex.soc.cores import uart

from liteluna.stream import USBStreamer


def add_usbbone(soc, ulpi, name="usbbone", with_blinky=False):
    soc.check_if_exists(name)
    jtagbone_phy = USBStreamer(platform, self.ulpi, with_blinky=True)
    usbbone_phy = USBStreamer(platform, ulpi, with_blinky=with_blinky)
    usbbone = uart.UARTBone(phy=usbbone_phy, clk_freq=60e6, cd="usb")
    setattr(soc.submodules, f"{name}_phy", usbbone_phy)
    setattr(soc.submodules, name, usbbone)
    soc.bus.add_master(name=name, master=usbbone.wishbone)
