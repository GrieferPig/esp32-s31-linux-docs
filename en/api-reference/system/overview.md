# System architecture

Linux runs on both ESP32-S31 high-performance cores with Sv32 virtual memory.
The supplied configuration executes kernel code from mapped flash and uses
16 MiB PSRAM for writable data and applications.

## Main components

| Component | Role |
|---|---|
| ROM and SPL | Start the chip and initialize memory |
| OpenSBI | Provide machine-mode services to Linux and U-Boot |
| U-Boot | Start the Linux image with its device tree |
| Linux | Run applications and manage processors, memory and devices |
| Buildroot | Build the root filesystem and command-line tools |
| Radio module and payload | Provide the Wi-Fi and Bluetooth runtime |
| LP firmware | Run mailbox and wakeup tasks on the low-power core |

Boot passes through ROM, SPL, OpenSBI and U-Boot before Linux starts BusyBox
userspace. [Boot process](boot-chain.md) describes the address handoffs and
startup services.

## Memory and filesystems

Execute in place (XIP) keeps kernel code in mapped flash, leaving PSRAM for
writable data and applications. Internal SRAM holds firmware data, radio
allocations and DMA descriptors. Exact regions and ownership are in
[Memory map](../../hw-reference/memory-map.md).

The root uses a SquashFS image with a JFFS2-backed writable overlay. For what
persists across reboot, package-owned file replacement and temporary storage,
see [Configuration](../../resources/configuration.md).

## Peripherals

Applications use Linux interfaces such as GPIO character devices, I2C, SPI,
ALSA and sockets. `s31-overlay` enables optional peripherals and selects their
pins. The standard [build configuration](../../get-started/build-configuration.md)
includes the native peripheral drivers; external devices can require additional
drivers and board wiring.

## Radio and low-power core

Wi-Fi and Bluetooth share a Linux radio module and payload. Its common worker,
when used, runs on HP core 0; Wi-Fi-only SoftMAC uses native task servicing.
Frontend receive NAPI and I/O target HP core 1, with HP core 0 as the fallback
when core 1 is offline. Payload compatibility tasks preserve requested affinity.
The [interrupts and SMP reference](interrupts-smp.md) explains these execution and
IRQ-routing boundaries. Bluetooth normally uses BTstack through `/dev/s31-hci`.

LP firmware is loaded by Linux remoteproc and handles mailbox, timer and GPIO
wakeup requests. See the [radio reference](../radio/index.md) and
[LP reference](../lp-core/index.md) for their separate interfaces.
