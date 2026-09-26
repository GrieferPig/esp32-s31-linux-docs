# LP firmware development

LP firmware runs on the low-power core and communicates with Linux through the
hardware mailbox. The project builds it with the ESP-IDF environment used in
[Build from source](../get-started/build-from-source.md).

## Build the firmware

From the project root, run:

```sh
make lp-firmware
```

The build stages the ELF for remoteproc under the firmware name
`esp32s31/s31-lp-core.elf`. Rebuild the root filesystem to include it in an image:

```sh
make rootfs
```

After installing the updated image, check startup with:

```sh
s31-lpctl status
s31-lpctl ping
```

## Place code and data

LP SRAM starts at `0x2E000000` and is 32 KiB in size. Keep these shared regions
free in the linker layout:

| Region | Address range, end exclusive |
|---|---|
| OpenSBI suspend snapshot | `0x2E002000`–`0x2E007000` |
| Sleep-control reservation | `0x2E007C00`–`0x2E008000` |

Check the ELF load segments, data, and stack placement against both regions
when increasing firmware size.

## Update the mailbox protocol

The parent header `shared/s31_lp_protocol.h` includes the Linux protocol
header at `include/linux/soc/espressif/esp32s31-lp-protocol.h`.

Firmware publishes READY after startup and validates sleep requests before
arming them. Write result, state, and wake data before publishing the response
CRC. Message codes, sequence rules, structure layout, and CRC coverage are
listed in the [LP reference](../api-reference/lp-core/index.md).

When changing the protocol, update its Linux, firmware, and OpenSBI consumers
together. The current system-suspend mismatch is described in
[Power management](power-management.md).

## Add a peripheral

LP peripheral registers are protected by the peripheral PMS controller. Add
the required register-window permissions in the remoteproc driver before
using a new block from LP firmware.

GPIO tests use RTCIO ownership and software sampling. Keep the existing
handover and release sequence when adding another GPIO operation.
