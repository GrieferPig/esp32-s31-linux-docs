# Writing applications

Applications run in a small Buildroot environment with musl libc and a BusyBox
shell. Hardware is accessed through Linux device files, sockets, and sysfs.

## Build a C program

Create `hello.c` on your development computer:

```c
#include <stdio.h>

int main(void)
{
    puts("Hello from ESP32-S31 Linux!");
    return 0;
}
```

From the project root, compile it with the Linux toolchain:

```sh
toolchain/riscv32-esp-linux-musl/bin/riscv32-esp-linux-musl-gcc \
  -Os -mabi=ilp32 hello.c -o hello
```

To include the program in an image, add it to the Buildroot package as described
in [Adding a userspace tool](../../api-guides/adding-a-userspace-tool.md).
The [ISA and ABI reference](../../hw-reference/isa.md) covers compiler settings
for optimized code.

## Access hardware

| Hardware | Application interface |
|---|---|
| UART | TTY and termios |
| GPIO | GPIO character devices and libgpiod |
| I2C | `/dev/i2c-*` |
| SPI | `/dev/spidev*` |
| Audio | ALSA PCM |
| CAN | SocketCAN |
| Wi-Fi and Ethernet | Network sockets |
| Analog inputs and outputs | IIO |
| Watchdog | Linux watchdog device |
| LP core | `s31-lpctl` and `/dev/s31-lp` |
| Bluetooth, default setup | BTstack and `/dev/s31-hci` |

Enable the required [overlay](../../resources/overlay-catalog.md) before
opening a peripheral. The [peripheral reference](../peripherals/index.md)
contains command-line examples.

## Files and settings

Save small configuration files under `/etc/esp32-conf`. Files in `/var/lib`
also survive a restart through the writable root layer. Temporary files belong
in `/tmp`, and runtime status files belong in `/run`.

The writable flash partition is 640 KiB. Use an SD card or USB drive for large
data files and logs. See [Configuration](../../resources/configuration.md).

## Available tools

The image includes board configuration, overlay, LP, and test utilities.
Their syntax is listed in the [command reference](../../resources/cli-reference.md).

Other packages can be added through Buildroot. Post-build script can remove some files from the image, so check `build/buildroot/target` when selecting applications.
