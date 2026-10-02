# Writing applications

Applications run in a small Buildroot environment with musl libc and a BusyBox
shell. Hardware is accessed through Linux device files, sockets, and sysfs.

## Build, install, and run a C program

Complete [Build from source](../../get-started/build-from-source.md) first,
including the ESP-IDF environment. Run the host commands below from the project
root. The rootfs-only updates below require a board already running the selected
kernel configuration and build profile. To change either, follow
[Build profiles](../../get-started/build-profiles.md) first. Keep the same profile
in the environment while building these applications.

Create `hello.c` on your development computer:

```c
#include <stdio.h>

int main(void)
{
    puts("Hello from ESP32-S31 Linux!");
    return 0;
}
```

Compile it, put the binary in the board filesystem overlay, and build and flash
the updated rootfs. Replace `/dev/ttyUSB0` with the board's port and close the
serial monitor before flashing:

```sh
toolchain/riscv32-esp-linux-musl/bin/riscv32-esp-linux-musl-gcc \
  -Os -mabi=ilp32 hello.c -o hello
install -D -m 0755 hello \
  buildroot-external/board/esp32-s31/overlay/usr/bin/hello
make rootfs
make flash-existing-rootfs PORT=/dev/ttyUSB0
```

The [flash-existing-rootfs target](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L532-L536) writes the image produced by `make rootfs` without another
build. Reopen the serial console after flashing, log in, and run on the board:

```sh
hello
```

The program prints `Hello from ESP32-S31 Linux!`. This workflow uses the existing
flashing connection; the default image has no SSH server. For repeated development
or applications with dependencies, use the [Buildroot package
example](../../api-guides/adding-a-userspace-tool.md) instead of maintaining a
precompiled binary in the overlay.

## Use libesp-simd

`libesp-simd` exposes the port's XespV 2.2 memory and string operations through
`esp_simd.h`. The [library package](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/package/esp-simd/esp-simd.mk#L26-L42) installs its header and libraries into
`build/buildroot/staging`, and the shared library into the image.

Create `simd-demo.c` on the host:

```c
#include <stdio.h>
#include <string.h>
#include <esp_simd.h>

int main(void)
{
    const char message[] = "SIMD copy";
    char copy[sizeof(message)];
    int rc = esp_simd_init();

    if (rc) {
        fprintf(stderr, "esp_simd_init: %s\n", strerror(-rc));
        return 1;
    }
    esp_simd_memcpy(copy, message, sizeof(message));
    printf("CPU%d: %s\n", esp_simd_cpu(), copy);
    return strcmp(copy, message) != 0;
}
```

After a successful `make rootfs`, compile and install it with:

```sh
toolchain/riscv32-esp-linux-musl/bin/riscv32-esp-linux-musl-gcc \
  -Os -mabi=ilp32 -Ibuild/buildroot/staging/usr/include \
  simd-demo.c -Lbuild/buildroot/staging/usr/lib -lesp-simd -o simd-demo
install -D -m 0755 simd-demo \
  buildroot-external/board/esp32-s31/overlay/usr/bin/simd-demo
make rootfs
make flash-existing-rootfs PORT=/dev/ttyUSB0
```

Run `simd-demo` from the board console. With initialization successful, it prints
`CPU1: SIMD copy`.

The library constructor attempts to pin the initial thread to CPU1 before
`main()`. SIMD operations also initialize each calling thread on its first use.
`esp_simd_init()` returns zero on success or a negative errno value on affinity
failure; the wrappers use scalar fallbacks if initialization fails. This affinity
change applies to the whole calling thread, including its non-SIMD work. Once
initialized, do not move that thread to CPU0 or broaden its CPU affinity: the
library caches successful initialization and does not recheck later affinity
changes. For raw instructions and compiler ABI choices, see
[ISA and ABI](../../hw-reference/isa.md).

The [library implementation](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/rootfs/esp_simd.c)
and `rootfs/s31_string_bench.c` provide more examples. A Buildroot package using
the library should select `BR2_PACKAGE_ESP_SIMD`, add `esp-simd` to its package
dependencies, and link with `-lesp-simd`.

## Access hardware

These interfaces are available when the corresponding kernel driver and hardware
are enabled. The lean profile omits several optional peripheral drivers.

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

Enable an optional peripheral's [overlay](../../resources/overlay-catalog.md)
before opening it. The [peripheral reference](../peripherals/index.md) contains
command-line examples.

## Files, settings, and other tools

See [Configuration](../../resources/configuration.md) for persistent and temporary
storage. Deployment exceptions for package-owned files are documented in
[Adding a userspace tool](deploy-files-that-must-survive-reboot).
The [command reference](../../resources/cli-reference.md) covers the included
board configuration, overlay, LP, and test utilities.
