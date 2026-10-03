# Developing the radio firmware

The radio firmware combines Espressif's Wi-Fi and Bluetooth libraries with the
port's OS adapters. Most code executes directly from the prelinked `radio.bin`
flash image, managed by the common Linux radio module in the rootfs.

Use this guide for changes inside `firmware/radio/`. Changes to Linux network
or Bluetooth interfaces usually belong in the kernel frontend instead; see
[Radio architecture](../api-reference/radio/architecture.md).

## Build the firmware

Set up the tools in [Build from source](../get-started/build-from-source.md),
then activate ESP-IDF and build from the parent project:

```sh
. "$IDF_PATH/export.sh"
export IDF_EXPORT="$IDF_PATH/export.sh"
make radio-linux-payload
```

This target first builds the ESP-IDF radio dependencies, then creates the
relocatable intermediate firmware and regenerates Linux import stubs. It does
not by itself produce the deployed flash image.

To build the kernel/module, rootfs, radio XIP image and verified manifest, run:

```sh
make image
```

This target produces the prelinked XIP payload `out/images/radio.bin`. The host prelinker uses the kernel's symbol addresses, and the
rootfs carries the matching Linux module. Deploy kernel, rootfs/module, and
radio image together after a firmware or kernel change. `make all` creates the
complete matched image set and manifest; `make flash-existing-all` writes its component
slots while preserving persist on boards already using the same layout. For
installation and data-backup instructions, follow
[Flash and first boot](../get-started/flash-and-first-boot.md).

## Change an operation

Follow the existing Wi-Fi or HCI path through the frontend, Linux radio core,
and firmware entry point. Keep application-facing calls in the frontend and
hardware-library calls inside the firmware.

When adding a firmware entry point, update its export and the loader's import
or export handling as needed, then regenerate the stubs with the normal build
target. That build also regenerates `out/generated/radio-kernel-symbols.txt`
for the kernel's `CONFIG_TRIM_UNUSED_KSYMS` export retention. Do not hand-edit
the generated stubs or whitelist. Changes to structures or calling conventions
also need an ABI update on the components that exchange them.

Radio code can run from a worker or an interrupt callback. Keep interrupt work
short, and copy data that must outlive a callback into storage owned by its
consumer.

## Find the implementation

| Source | Role |
|---|---|
| `firmware/radio/radio_stack.c` | ESP-IDF operations and raw Wi-Fi frame transport |
| `firmware/radio/s31_rtos/` | Task and synchronization adapters |
| `firmware/radio/Makefile` | Link inputs and generated import stubs |
| `drivers/platform/esp32s31-radio-smode.c` in Linux | Command queue, workers, and SRAM allocation |
| `drivers/platform/esp32s31-radio-loader.c` in Linux | XIP image validation and entry-point wrappers |
| `drivers/net/wireless/espressif/esp32s31_softmac.c` in Linux | mac80211 station frontend |
| `drivers/bluetooth/hci_esp32s31.c` in Linux | Direct HCI and Linux HCI frontends |

## Check memory use

The XIP payload's writable data/BSS lives in a 40 KiB built-in kernel RAM
arena in PSRAM. Radio heap allocations, task stacks, buffers, and selected
Wi-Fi hot code consume internal SRAM. Keep both budgets within their separate
limits. Use `radio_health` for heap usage and worker state; inspect `dmesg` for
allocation failures, which do not have a dedicated health counter. The memory regions are described in
[Memory map](../hw-reference/memory-map.md).

## Test the update

Start with the changed mode, then check Wi-Fi and Bluetooth together. Exercise
startup, traffic, queue pressure, shutdown, and reloading the radio module.
The [HIL guide](../contribute/testing-hil.md) includes radio peer tests.

For a separately packaged radio archive, run `make radio-package`. See
[Releases and licensing](../contribute/release-and-legal.md) before distributing
firmware that includes third-party libraries.
