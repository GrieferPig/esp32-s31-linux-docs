# Introduction

`esp32-s31-linux` ports an embedded Linux system to the ESP32-S31. It runs a
32-bit RISC-V kernel on both high-performance CPU cores and includes a
BusyBox shell, Wi-Fi and Bluetooth support, and (most) drivers for on-chip peripherals.

The port uses Linux 6.18, U-Boot, OpenSBI, and Buildroot.

## Feature support

The port is under active development. See
[Feature support](../resources/support-matrix.md) for available drivers and
current limitations.

## Quick start

To install a precompiled image, follow [Flash and first boot](flash-and-first-boot.md).

To build a custom image from source, follow [Build from source](build-from-source.md).

After booting, run `esp32-config` to configure the board. The
[overlay catalog](../resources/overlay-catalog.md) and
[peripheral examples](../api-reference/peripherals/index.md) are good next steps.
