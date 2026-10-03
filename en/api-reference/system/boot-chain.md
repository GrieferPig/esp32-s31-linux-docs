# Boot process

The board starts Linux through ROM, SPL, OpenSBI, and U-Boot. This page explains
what each stage does and which files to inspect when boot stops early.

## 1. ROM and SPL

The on-chip ROM starts after reset. It can accept firmware through the download
connection or load SPL from flash.

`out/images/spl_app.bin` contains SPL in the image format expected by ROM. SPL
initializes the hardware needed for boot and loads the U-Boot FIT image,
`out/images/u-boot.itb`. The 48 KiB SPL slot starts at raw `0x002000`, after the
mandatory 8 KiB FlashEncryption reservation. The FIT starts immediately after
SPL at raw `0x00E000`.

## 2. OpenSBI and U-Boot

SPL enters OpenSBI in machine mode and supplies the address of U-Boot proper.
OpenSBI initializes its platform services and starts U-Boot in supervisor mode.
It remains available to handle Linux SBI calls after boot.

Boot maps all 16 MiB of raw flash linearly at physical `0x40000000`.
The mapped FIT address is `0x4000E000`, with the OpenSBI XIP payload at
`0x4000E400`.

U-Boot starts the kernel with the Linux device tree. The default boot command
uses these mapped addresses:

```text
booti 0x40400000 - 0x4005E000
```

The first address is the kernel and the second is the device tree. The kernel
start is aligned to a 4 MiB Sv32 megapage boundary. Preserve that alignment
when modifying the XIP layout. Flashing uses the raw offsets listed in
[Flash layout](../../hw-reference/flash-layout.md).

## 3. Linux and the root filesystem

Linux initializes memory, interrupts, timers, and device drivers, then starts
`/init` from the root filesystem.

The early init script mounts the persistent JFFS2 partition and combines it
with the SquashFS base using OverlayFS. It then restores saved device-tree
overlays, loads the selected radio mode, and starts BusyBox init.

If the persistent filesystem fails to mount, the script prints an error and
continues in recovery with the read-only base system. Recovery prepares
volatile `/run`, `/tmp`, and `/var/log`; persistent settings are unavailable.
The early overlay-restore and radio-load steps are skipped on this path.
See [Debugging](../../api-guides/debugging.md) for the checks to run in that case.

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
| `rootfs.sqfs` | Early init, BusyBox, applications, and the Linux radio module |
| `radio.bin` | Prelinked flash-XIP radio payload matched to the kernel/module |

For flashing commands, see [Flash and first boot](../../get-started/flash-and-first-boot.md).
