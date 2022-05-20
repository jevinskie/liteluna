#!/usr/bin/env python3

# This file is derived from LUNA.
#
# Copyright (c) 2020 Great Scott Gadgets <info@greatscottgadgets.com>
# Copyright (c) 2022 Jevin Sweval <jevinsweval@gmail.com>
# SPDX-License-Identifier: BSD-3-Clause

from amaranth import Cat, Elaboratable, Module
from luna.usb2 import USBDevice, USBStreamInEndpoint, USBStreamOutEndpoint
from usb_protocol.emitters import DeviceDescriptorCollection


class USBStreamerDevice(Elaboratable):
    BULK_ENDPOINT_NUMBER = 1
    MAX_BULK_PACKET_SIZE = 512

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

        m.submodules.car = platform.clock_domain_generator()

        ulpi = platform.request(platform.default_usb_connection)
        m.submodules.usb = usb = USBDevice(bus=ulpi)

        descriptors = self.create_descriptors()
        usb.add_standard_control_endpoint(descriptors)

        stream_out_ep = USBStreamOutEndpoint(
            endpoint_number=self.BULK_ENDPOINT_NUMBER,
            max_packet_size=self.MAX_BULK_PACKET_SIZE,
        )
        usb.add_endpoint(stream_out_ep)

        stream_in_ep = USBStreamInEndpoint(
            endpoint_number=self.BULK_ENDPOINT_NUMBER,
            max_packet_size=self.MAX_BULK_PACKET_SIZE,
        )
        usb.add_endpoint(stream_in_ep)

        stream_in = stream_in_ep.stream
        stream_out = stream_out_ep.stream

        m.d.comb += [
            stream_in.payload.eq(~stream_out.payload),
            stream_in.valid.eq(stream_out.valid),
            stream_in.first.eq(stream_out.first),
            stream_in.last.eq(stream_out.last),
            stream_out.ready.eq(stream_in.ready),
            usb.connect.eq(1),
        ]

        return m


if __name__ == "__main__":
    pass
