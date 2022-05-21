#!/usr/bin/env python3

# This file is derived from LUNA.
#
# Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
# Copyright (c) 2022 Jevin Sweval <jevinsweval@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import amaranth.cli
from amaranth import Cat, Elaboratable, Module, Signal
from luna.gateware.interface.ulpi import ULPIInterface
from luna.usb2 import USBDevice, USBStreamInEndpoint, USBStreamOutEndpoint
from usb_protocol.emitters import DeviceDescriptorCollection


class USBBulkStreamerDevice(Elaboratable):
    BULK_ENDPOINT_NUMBER = 1
    MAX_BULK_PACKET_SIZE = 512

    def __init__(self):
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
        self.ulpi_clk = Signal()
        self.ulpi_nxt = Signal()
        self.ulpi_stp = Signal()
        self.ulpi_dir = Signal()
        self.ulpi_rst = Signal()

        self.connect = Signal()

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

        descriptors = self.create_descriptors()
        usb.add_standard_control_endpoint(descriptors)

        usb.add_endpoint(self.stream_out_ep)
        usb.add_endpoint(self.stream_in_ep)

        stream_out = self.stream_out_ep.stream
        stream_in = self.stream_in_ep.stream

        m.d.comb += usb.connect.eq(self.connect)

        m.d.comb += [
            self.ulpi_data_i.eq(self.ulpi.data.i),
            self.ulpi_data_o.eq(self.ulpi.data.o),
            self.ulpi_data_oe.eq(self.ulpi.data.oe),
            self.ulpi_clk.eq(self.ulpi.clk),
            self.ulpi_nxt.eq(self.ulpi.nxt),
            self.ulpi_stp.eq(self.ulpi.stp),
            self.ulpi_dir.eq(self.ulpi.dir.i),
            self.ulpi_rst.eq(self.ulpi.rst),
        ]

        m.d.comb += [
            self.stream_out_payload.eq(stream_out.payload),
            self.stream_out_valid.eq(stream_out.valid),
            self.stream_out_ready.eq(stream_out.ready),
            self.stream_out_first.eq(stream_out.first),
            self.stream_out_last.eq(stream_out.last),
        ]

        m.d.comb += [
            self.stream_in_payload.eq(stream_in.payload),
            self.stream_in_valid.eq(stream_in.valid),
            self.stream_in_ready.eq(stream_in.ready),
            self.stream_in_first.eq(stream_in.first),
            self.stream_in_last.eq(stream_in.last),
        ]

        return m


if __name__ == "__main__":
    streamer = USBBulkStreamerDevice()
    amaranth.cli.main(
        streamer,
        name="bulk_streamer",
        ports=[
            streamer.ulpi_clk,
            streamer.ulpi_rst,
            streamer.ulpi_data_i,
            streamer.ulpi_data_o,
            streamer.ulpi_data_oe,
            streamer.ulpi_nxt,
            streamer.ulpi_stp,
            streamer.ulpi_dir,
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
        ],
    )
