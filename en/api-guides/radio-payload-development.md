# Developing the radio firmware

The radio firmware combines Espressif's Wi-Fi and Bluetooth libraries with the
port's OS adapters. Linux loads it from `radio.sqfs` through the common radio
module. Use this guide for changes inside `firmware/radio/`; Linux networking
and Bluetooth interface changes usually belong in the kernel frontends.
[Radio architecture](../api-reference/radio/architecture.md) describes their
relationship.

## Build and deploy

Set up [Build from source](../get-started/build-from-source.md), keep your selected
build profile exported, and run from the parent project on the host:

```sh
. "$IDF_PATH/export.sh"
export IDF_EXPORT="$IDF_PATH/export.sh"
make radio-fs
make flash-existing-radio PORT=/dev/ttyUSB0
```

Replace the serial port and close its monitor before flashing. `radio-fs`
builds the ESP-IDF dependencies, payload, Linux module, and rootfs dependencies,
then packages `build/radio.sqfs`. The flash command writes that existing radio
image without rebuilding it.

Use this radio-only update with the matching kernel already on the board. If
you changed kernel code, configuration, or an interface used by the module,
update the corresponding kernel and other images with `make flash-all` instead.
See [Flash and first boot](../get-started/flash-and-first-boot.md) for image
updates.

The [parent Makefile](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L202-L284) also provides individual build stages:

| Target | Result |
|---|---|
| `make radio-idf-deps` | Build the ESP-IDF library dependencies |
| `make radio-linux-payload` | Build `build/esp32s31-radio-fw-v1.o` and regenerate kernel import stubs |
| `make radio-fs` | Rebuild dependencies and package `build/radio.sqfs` |

## Find the implementation

| File or directory | Role |
|---|---|
| `firmware/radio/radio_stack.c` | Wi-Fi/Bluetooth operations calling ESP-IDF libraries |
| `firmware/radio/s31_rtos/` | Firmware-side task and synchronization adapters |
| `firmware/radio/Makefile` | Payload link inputs, retained exports, and import-stub generation |
| `linux-esp32-s31/drivers/platform/esp32s31-radio-smode.c` | Linux radio command queue, workers, and SRAM allocation |
| `linux-esp32-s31/drivers/platform/esp32s31-radio-loader.c` | ELF loading, export resolution, and entry-point wrappers |
| `linux-esp32-s31/drivers/net/wireless/espressif/esp32s31_wifi.c` | cfg80211/netdev frontend |
| `linux-esp32-s31/drivers/bluetooth/hci_esp32s31.c` | Direct HCI and Linux HCI frontends |

### Example: follow a station connection

Start with `s31_cfg_connect()` in the [Wi-Fi frontend](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/net/wireless/espressif/esp32s31_wifi.c#L636-L689). It validates the cfg80211
request and calls `esp32s31_radio_wifi_connect()` through CPU0 work. The radio
core queues a connect command, copies its parameters to SRAM, and starts
`s31_radio_wifi_connect_task()`.

The loader wrapper resolves that function to the payload entry point of the
same name in [radio_stack.c](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/radio/radio_stack.c#L1246-L1303). That function prepares the ESP-IDF
station configuration and submits the connection. The result returns through
`s31_radio_wifi_connected()` and the frontend's registered callback.

For a new entry point, follow this existing chain: retain the exported symbol
in the payload link, add the loader's export lookup and wrapper, and update the
calling code. Regenerate `esp32s31-radio-imports.S` with
`make radio-linux-payload`; do not maintain generated stubs by hand. Shared
structure or calling-convention changes must be made in every component using
them, with the applicable ABI version updated when compatibility changes.

Radio callbacks may run in interrupt context. Keep that work short and copy
data into storage owned by the consumer if it must outlive the callback. The
common callback contract is in `include/linux/esp32s31-radio.h` in the kernel.

## Check memory and runtime status

Radio buffers and OS-adapter allocations use reserved internal-SRAM pools.
The ELF loader separately allocates the loaded firmware, including its mutable
sections; the fixed SRAM pools do not describe all firmware memory. See
[Memory map](../hw-reference/memory-map.md).

The [radio reference](radio-status) shows how to
read `radio_health`. The [attribute implementation](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-module.c#L27-L63) reports heap usage, peak usage, total capacity, packet
drops, initialization results, and worker activity. Allocation failures are
also reported in kernel diagnostics; `radio_health` has no dedicated allocation
failure counter. Check `dmesg` alongside it.

## Test the update

After booting, use [Wi-Fi and Bluetooth setup](../user-guides/networking.md) to
exercise the changed mode, then both services together. Check startup, traffic,
queue pressure, shutdown, and reloading. The [HIL guide](../contribute/testing-hil.md)
includes peer tests; record which tests you actually ran and their results.

For a separate radio archive, run `make radio-package`. See
[Releases and licensing](../contribute/release-and-legal.md) before distributing
firmware containing third-party libraries.
