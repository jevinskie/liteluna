#!/usr/bin/env python3

# This file is derived from LUNA.
#
# Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
# Copyright (c) 2022 Jevin Sweval <jevinsweval@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

import amaranth.cli
from amaranth import Cat, Elaboratable, Module
from luna.gateware.interface.ulpi import ULPIInterface
from luna.usb2 import USBDevice, USBStreamInEndpoint, USBStreamOutEndpoint
from usb_protocol.emitters import DeviceDescriptorCollection

from liteluna.luna_cores.external_car import ExternalClockAndResetController


class USBBulkStreamerDevice(Elaboratable):
    BULK_ENDPOINT_NUMBER = 1
    MAX_BULK_PACKET_SIZE = 512

    def __init__(self):
        self.stream_out_ep = USBStreamOutEndpoint(
            endpoint_number=self.BULK_ENDPOINT_NUMBER,
            max_packet_size=self.MAX_BULK_PACKET_SIZE,
        )
        self.stream_out = self.stream_out_ep.stream

        self.stream_in_ep = USBStreamInEndpoint(
            endpoint_number=self.BULK_ENDPOINT_NUMBER,
            max_packet_size=self.MAX_BULK_PACKET_SIZE,
        )
        self.stream_in = self.stream_in_ep.stream

        self.ulpi = ULPIInterface()

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

        m.submodules.car = ExternalClockAndResetController()

        m.submodules.usb = usb = USBDevice(bus=self.ulpi, handle_clocking=False)

        descriptors = self.create_descriptors()
        usb.add_standard_control_endpoint(descriptors)

        usb.add_endpoint(self.stream_out_ep)
        usb.add_endpoint(self.stream_in_ep)

        stream_in = self.stream_in
        stream_out = self.stream_out

        m.d.comb += [
            stream_in.payload.eq(stream_out.payload),
            stream_in.valid.eq(stream_out.valid),
            stream_in.first.eq(stream_out.first),
            stream_in.last.eq(stream_out.last),
            stream_out.ready.eq(stream_in.ready),
            usb.connect.eq(1),
        ]

        print(m)

        return m


if __name__ == "__main__":
    streamer = USBBulkStreamerDevice()
    amaranth.cli.main(
        streamer, ports=[streamer.ulpi.data.i, streamer.stream_in.payload]
    )
