# Boot process

The board starts Linux through ROM, SPL, OpenSBI, and U-Boot. This page explains
what each stage does and which files to inspect when boot stops early.

## 1. ROM and SPL

The supplied image is prepared for the ROM's normal flash-boot path. The
parent build uses `esptool --chip esp32s31 elf2image` to package SPL as
`build/spl_app.bin`, and the flashing recipe writes it through the download
connection. See [image packaging](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L193-L199)
and the [flash recipe](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L494-L499).

SPL initializes the memory and clocks needed for boot and loads the U-Boot
FIT image, `build/u-boot.itb`. Its [board initialization](https://github.com/GrieferPig/u-boot-esp32-s31/blob/06fe89c93ed52349f60120c77efe3018c1e6b29f/board/espressif/esp32s31/spl.c#L59-L90)
selects NOR as the boot device.

## 2. OpenSBI and U-Boot

SPL enters OpenSBI in machine mode and supplies the address of U-Boot proper.
OpenSBI initializes its platform services and starts U-Boot in supervisor mode.
It remains available to handle Linux SBI calls after boot.

U-Boot starts the kernel with the Linux device tree. The default boot command
uses these mapped addresses:

```text
booti 0x40400000 - 0x40200000
```

The first address is the kernel and the second is the device tree. SPL maps
raw flash offset `0x100000` to CPU address `0x40000000`, so these correspond to
raw offsets `0x500000` and `0x300000`. See
[Flash layout](../../hw-reference/flash-layout.md#raw-offsets-and-mapped-addresses)
for the address conversion and partition table.

## 3. Linux and the root filesystem

Linux initializes memory, interrupts, timers, and device drivers, then starts
`/init` from the root filesystem.

The early init script assembles the writable root filesystem, restores saved
device-tree overlays, loads the selected radio mode, and starts BusyBox init.
The filesystem layout and saved settings are described in
[Configuration](../../resources/configuration.md).

If the persistent filesystem fails to mount, the script prints an error and
starts BusyBox init from the read-only base. This bypasses the early overlay
restore and radio-load steps, so those devices may be unavailable. See
[Debugging](../../api-guides/debugging.md) for the checks to run in that case.

## 4. Services and serial login

BusyBox starts the board services and the serial login. Services run through
`rcS`, and their output is saved in `/run/rcS.log`. The login prompt may appear
while those services are still starting.

```sh
cat /run/rcS.log
test -e /run/rcS.done && cat /run/rcS.status
```

## Boot files

| File | Stage |
|---|---|
| `spl_app.bin` | ROM-loadable SPL |
| `u-boot.itb` | OpenSBI and U-Boot |
| `esp32s31_generic.dtb` | Linux hardware description |
| `xipImage` | Linux kernel |
| `rootfs.sqfs` | Early init, BusyBox, and applications |
| `radio.sqfs` | Radio module and external firmware |

For flashing commands, see [Flash and first boot](../../get-started/flash-and-first-boot.md).
