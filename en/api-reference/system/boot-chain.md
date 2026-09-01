# Boot Chain and Storage

## Boot sequence

1. ROM selects normal boot or serial download mode and enters U-Boot SPL.
2. SPL establishes the clock and PSRAM state required by later stages.
3. U-Boot loads its FIT, including OpenSBI, U-Boot proper, and associated data.
4. U-Boot supplies the base DTB and kernel command line to OpenSBI.
5. OpenSBI starts the high-performance harts and enters Linux in S-mode.
6. Linux executes `xipImage` from NOR and mounts the read-only SquashFS root.
7. Early userspace mounts persistent storage and optionally loads the separate
   radio filesystem and device-tree overlays.

OpenSBI writable state is in internal SRAM; its executable and read-only
sections may remain in the mapped FIT. U-Boot must not overwrite Linux reserved
memory or hand off an address that conflicts with the XIP window.

## NOR partition layout

| Offset | Artifact | Behavior |
|---:|---|---|
| `0x002000` | `spl_app.bin` | ROM-loadable SPL application image |
| `0x100000` | `u-boot.itb` | U-Boot/OpenSBI FIT |
| `0x300000` | `esp32s31_generic.dtb` | Base Linux device tree |
| `0x310000` | `radio.sqfs` | Radio payload and redistributable runtime files |
| `0x500000` | `xipImage` | XIP Linux kernel image |
| `0xB30000` | `persist.jffs2` | Writable persistent data |
| `0xBD0000` | `rootfs.sqfs` | Read-only Linux root filesystem |
| `0x1000000` | end of flash | End of the 16 MiB address space |

Normal full-image generation deliberately excludes the persistent partition.
An update workflow must erase or write `persist.jffs2` only when explicitly
requested. The canonical values are maintained in
`configs/esp32s31-layout.cfg` in the parent repository.

## Filesystem behavior

The root filesystem is immutable SquashFS. Persistent state is mounted from
JFFS2 and overlaid or bind-mounted by early userspace where configured. The
radio image is separate so payload licensing and update policy do not become
implicit properties of the root filesystem.
