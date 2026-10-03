# System architecture

Linux runs on both ESP32-S31 high-performance cores. It uses the Sv32 MMU for
virtual memory, flash for kernel code, and PSRAM for writable data and
applications.

## Main components

| Component | What it does |
|---|---|
| ROM and SPL | Start the chip and initialize memory |
| OpenSBI | Provide machine-mode services to Linux and U-Boot |
| U-Boot | Select the Linux image and device tree, then start the kernel |
| Linux | Run applications and manage processors, memory, and devices |
| Buildroot | Build the root filesystem and command-line tools |
| Radio module and firmware | Provide Wi-Fi and Bluetooth |
| LP firmware | Run mailbox and wakeup tasks on the low-power core |

The boot sequence is:

```text
ROM → SPL → OpenSBI → U-Boot → Linux → BusyBox userspace
```

See [Boot process](boot-chain.md) for the steps involved.

## Memory and filesystems

The kernel executes directly from mapped flash, a feature called execute in
place (XIP). This leaves more of the 16 MiB PSRAM available for applications.
Internal SRAM holds firmware data, radio allocations, and DMA descriptors.

The root filesystem combines a compressed SquashFS image with a small writable
JFFS2 partition. Settings and other saved files go into the writable layer.
Temporary files under `/tmp`, `/run`, and `/var/log` use RAM.

See [Memory map](../../hw-reference/memory-map.md) and
[Configuration](../../resources/configuration.md) for details.

## Peripherals

Applications use Linux interfaces such as GPIO character devices, I2C, SPI,
ALSA, and network sockets. Use `s31-overlay` to enable optional peripherals
and choose their pins. Most peripheral examples require the full-peripheral
[build configuration](../../get-started/build-configuration.md).

## Radio and low-power core

Wi-Fi and Bluetooth share a Linux radio module and firmware runtime. The
runtime executes on HP core 0, while Linux can schedule other work on either
core. Bluetooth normally uses BTstack through `/dev/s31-hci`.

The LP core runs its own firmware, loaded by Linux remoteproc. It exchanges
messages with Linux and handles timer and GPIO wakeup requests. See the
[radio reference](../radio/index.md) and [LP reference](../lp-core/index.md).
