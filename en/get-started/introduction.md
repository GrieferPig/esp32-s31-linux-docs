# Introduction

`esp32-s31-linux` ports an embedded Linux system to the ESP32-S31. It runs a
32-bit RISC-V kernel on both high-performance CPU cores and includes a
BusyBox shell, Wi-Fi and Bluetooth support, and drivers for on-chip peripherals.
The port uses Linux 6.18, U-Boot, OpenSBI, and Buildroot.

This is an experimental port. A successful normal boot, persistent flash
erase/write, and LP readiness have not been established for the current merged
image. Treat the guides as source-defined interfaces and validation procedures;
see the support matrix for the evidence available for each feature.

## Feature support

Every build uses the [full board configuration](build-configuration.md).
Optional hardware is enabled at runtime with device-tree overlays.
See [Feature support](../resources/support-matrix.md) for available interfaces,
evidence of testing, and current limitations.

## Quick start

To install a precompiled image and log in, follow
[Flash and first boot](flash-and-first-boot.md).

To build a custom image from the documented source revision, follow
[Build from source](build-from-source.md).

After booting, run `esp32-config` to configure the board. The
[overlay catalog](../resources/overlay-catalog.md) and
[peripheral examples](../api-reference/peripherals/index.md) are good next steps.
