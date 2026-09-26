# Developing the radio firmware

The radio firmware combines Espressif's Wi-Fi and Bluetooth libraries with the
port's OS adapters. Linux loads it from `radio.sqfs` through the common radio
module.

Use this guide for changes inside `firmware/radio/`. Changes to Linux network
or Bluetooth interfaces usually belong in the kernel frontend instead; see
[Radio architecture](../api-reference/radio/architecture.md).

## Build the firmware

Set up the tools in [Build from source](../get-started/build-from-source.md),
then activate ESP-IDF and build from the parent project:

```sh
. "$IDF_PATH/export.sh"
export IDF_EXPORT="$IDF_PATH/export.sh"
make radio-idf-deps
make radio-linux-payload
```

The first target builds the ESP-IDF libraries used by the radio. The second
creates the relocatable firmware and regenerates the Linux import stubs.

To rebuild the Linux module and package the radio filesystem, run:

```sh
make radio-fs
```

The result is `build/radio.sqfs`. Update Linux as well when your change affects
the module's imports or interface.

## Change an operation

Follow the existing Wi-Fi or HCI path through the frontend, Linux radio core,
and firmware entry point. Keep application-facing calls in the frontend and
hardware-library calls inside the firmware.

When adding a firmware entry point, update its export and the loader's import
or export handling as needed, then regenerate the stubs with the normal build
target. Changes to structures or calling conventions also need an ABI update
on the components that exchange them.

Radio code can run from a worker or an interrupt callback. Keep interrupt work
short, and copy data that must outlive a callback into storage owned by its
consumer.

## Check memory use

Static radio data, task stacks, and radio buffers share limited internal SRAM.
Use the driver's `radio_health` output to check heap usage and allocation
failures. The memory regions are described in
[Memory map](../hw-reference/memory-map.md).

## Test the update

Start with the changed mode, then check Wi-Fi and Bluetooth together. Exercise
startup, traffic, queue pressure, shutdown, and reloading the radio module.
The [HIL guide](../contribute/testing-hil.md) includes radio peer tests.

For a separately packaged radio archive, run `make radio-package`. See
[Releases and licensing](../contribute/release-and-legal.md) before distributing
firmware that includes third-party libraries.
