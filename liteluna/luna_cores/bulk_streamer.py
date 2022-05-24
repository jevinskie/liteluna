#!/usr/bin/env python3

# This file is derived from LUNA.
#
# Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
# Copyright (c) 2022 Jevin Sweval <jevinsweval@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import amaranth.cli
from amaranth import Cat, ClockSignal, Elaboratable, Module, ResetSignal, Signal
from luna.gateware.interface.ulpi import ULPIInterface
from luna.gateware.interface.utmi import UTMIInterface
from luna.usb2 import USBDevice, USBStreamInEndpoint, USBStreamOutEndpoint
from usb_protocol.emitters import DeviceDescriptorCollection


class StandaloneBlinky(Elaboratable):
    def __init__(self, leds: Signal):
        self.leds = leds

    def elaborate(self, platform):
        m = Module()

        clk_freq = 60e6
        timer = Signal(range(int(clk_freq // 2)), reset=int(clk_freq // 2) - 1)
        flops = Signal(len(self.leds))

        m.d.comb += Cat(self.leds).eq(flops)
        with m.If(timer == 0):
            m.d.usb += timer.eq(timer.reset)
            m.d.usb += flops.eq(~flops)
        with m.Else():
            m.d.usb += timer.eq(timer - 1)

        return m


class USBBulkStreamerDevice(Elaboratable):
    BULK_ENDPOINT_NUMBER = 1
    MAX_BULK_PACKET_SIZE = 512

    def __init__(self, with_blinky=False, with_utmi_la=False):
        self.with_blinky = with_blinky
        self.with_utmi_la = with_utmi_la

        self.stream_out_ep = USBStreamOutEndpoint(
            endpoint_number=self.BULK_ENDPOINT_NUMBER,
            max_packet_size=self.MAX_BULK_PACKET_SIZE,
        )
        self.stream_out_payload = Signal(8)
        self.stream_out_valid = Signal()
        self.stream_out_ready = Signal()
        self.stream_out_first = Signal()
        self.stream_out_last = Signal()

        self.stream_in_ep = USBStreamInEndpoint(
            endpoint_number=self.BULK_ENDPOINT_NUMBER,
            max_packet_size=self.MAX_BULK_PACKET_SIZE,
        )
        self.stream_in_payload = Signal(8)
        self.stream_in_valid = Signal()
        self.stream_in_ready = Signal()
        self.stream_in_first = Signal()
        self.stream_in_last = Signal()

        self.ulpi = ULPIInterface()
        self.ulpi_data_i = Signal(8)
        self.ulpi_data_o = Signal(8)
        self.ulpi_data_oe = Signal()
        self.ulpi_nxt = Signal()
        self.ulpi_stp = Signal()
        self.ulpi_dir = Signal()
        self.ulpi_rst = Signal()

        self.connect = Signal()

        if with_utmi_la:
            for name, nbit, _ in UTMIInterface().layout:
                setattr(self, f"utmi_{name}", Signal(nbit, name=f"utmi_{name}"))

        if with_blinky:
            self.led = Signal()

    def create_descriptors(self):
        descriptors = DeviceDescriptorCollection()

        with descriptors.DeviceDescriptor() as d:
            d.idVendor = 0x16D0
            d.idProduct = 0xF3B

            d.iManufacturer = "LiteX"
            d.iProduct = "liteluna bulk streamer"
            d.iSerialNumber = "no serial"

            d.bNumConfigurations = 1

        with descriptors.ConfigurationDescriptor() as c:
            with c.InterfaceDescriptor() as i:
                i.bInterfaceNumber = 0

                with i.EndpointDescriptor() as e:
                    e.bEndpointAddress = self.BULK_ENDPOINT_NUMBER
                    e.wMaxPacketSize = self.MAX_BULK_PACKET_SIZE

                with i.EndpointDescriptor() as e:
                    e.bEndpointAddress = 0x80 | self.BULK_ENDPOINT_NUMBER
                    e.wMaxPacketSize = self.MAX_BULK_PACKET_SIZE

        return descriptors

    def elaborate(self, platform):
        m = Module()

        m.submodules.usb = usb = USBDevice(bus=self.ulpi, handle_clocking=False)

        if self.with_blinky:
            m.submodules.blinky = StandaloneBlinky(self.led)

        descriptors = self.create_descriptors()
        usb.add_standard_control_endpoint(descriptors)

        usb.add_endpoint(self.stream_out_ep)
        usb.add_endpoint(self.stream_in_ep)

        stream_out = self.stream_out_ep.stream
        stream_in = self.stream_in_ep.stream

        m.d.comb += usb.connect.eq(self.connect)

        ulpi = self.ulpi

        m.d.comb += [
            ulpi.data.i.eq(self.ulpi_data_i),
            self.ulpi_data_o.eq(ulpi.data.o),
            self.ulpi_data_oe.eq(ulpi.data.oe),
            ulpi.clk.eq(ClockSignal("usb")),
            ulpi.nxt.eq(self.ulpi_nxt),
            self.ulpi_stp.eq(ulpi.stp),
            ulpi.dir.i.eq(self.ulpi_dir),
            self.ulpi_rst.eq(ulpi.rst),
        ]

        m.d.comb += [
            self.stream_out_payload.eq(stream_out.payload),
            self.stream_out_valid.eq(stream_out.valid),
            stream_out.ready.eq(self.stream_out_ready),
            self.stream_out_first.eq(stream_out.first),
            self.stream_out_last.eq(stream_out.last),
        ]

        m.d.comb += [
            stream_in.payload.eq(self.stream_in_payload),
            stream_in.valid.eq(self.stream_in_valid),
            self.stream_in_ready.eq(stream_in.ready),
            stream_in.first.eq(self.stream_in_first),
            stream_in.last.eq(self.stream_in_last),
        ]

        if self.with_utmi_la:
            for name, _, _ in UTMIInterface().layout:
                m.d.comb += getattr(self, f"utmi_{name}").eq(getattr(usb.utmi, name))

        return m

    @staticmethod
    def get_instance_and_ports(with_blinky=False, with_utmi_la=False):
        streamer = USBBulkStreamerDevice(with_blinky=with_blinky, with_utmi_la=with_utmi_la)
        streamer_ports = [
            streamer.ulpi_data_i,
            streamer.ulpi_data_o,
            streamer.ulpi_data_oe,
            streamer.ulpi_nxt,
            streamer.ulpi_stp,
            streamer.ulpi_dir,
            streamer.ulpi_rst,
            streamer.connect,
            streamer.stream_out_payload,
            streamer.stream_out_valid,
            streamer.stream_out_ready,
            streamer.stream_out_first,
            streamer.stream_out_last,
            streamer.stream_out_first,
            streamer.stream_in_payload,
            streamer.stream_in_valid,
            streamer.stream_in_ready,
            streamer.stream_in_first,
            streamer.stream_in_last,
        ]
        if with_utmi_la:
            for name, _, _ in UTMIInterface().layout:
                streamer_ports.append(getattr(streamer, f"utmi_{name}"))
        if with_blinky:
            streamer_ports.append(streamer.led)
        return (streamer, streamer_ports)

    @staticmethod
    def emit_verilog(path, with_blinky=False, with_utmi_la=False):
        streamer, streamer_ports = USBBulkStreamerDevice.get_instance_and_ports(
            with_blinky=with_blinky, with_utmi_la=with_utmi_la
        )
        parser = amaranth.cli.main_parser()
        args = parser.parse_args(["generate", "-t", "v", path])
        amaranth.cli.main_runner(parser, args, streamer, name="bulk_streamer", ports=streamer_ports)


if __name__ == "__main__":
    streamer, streamer_ports = USBBulkStreamerDevice.get_instance_and_ports(with_utmi_la=True)
    amaranth.cli.main(
        streamer,
        name="bulk_streamer",
        ports=streamer_ports,
    )
