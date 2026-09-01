# Boot and Storage

## NOR Flash layout

The board contains 16 MiB of NOR Flash. The current slot offsets are defined by
[`configs/esp32s31-layout.cfg`](../configs/esp32s31-layout.cfg).

| Offset | Artifact | Behavior |
| ---: | --- | --- |
| `0x002000` | `spl_app.bin` | U-Boot SPL application image loaded by ROM |
| `0x100000` | `u-boot.itb` | FIT containing OpenSBI, U-Boot proper, and related data |
| `0x300000` | `esp32s31_generic.dtb` | Linux base device tree |
| `0x500000` | `xipImage` | Linux XIP kernel image |
| `0xB30000` | `persist.jffs2` | 640 KiB persistent writable layer |
| `0xBD0000` | `rootfs.sqfs` | Read-only SquashFS root filesystem |

The normal full image and `flash-all` omit the persistent slot, so firmware
updates preserve user configuration. `flash-persist` explicitly initializes
that slot. A full-chip erase destroys persistent state.

## Root filesystem

- `rootfs.sqfs` is the immutable lower layer.
- The persistent partition provides the OverlayFS `upper` and `work`
  directories.
- Early userspace mounts the persistent partition in a temporary staging tree
  and completes `pivot_root`.
- The staging mount is detached after the root switch, so the running system
  does not expose a raw `/persist` backend.
- Applications read and write configuration through standard paths in the
  merged root. Project policy files reside under `/etc/esp32-conf`.

## Flash access behavior

- NOR Flash normally cannot be read directly while an erase or program
  operation is in progress.
- The Flash device used by the current module supports auto-suspend, allowing
  reads to preempt long erase or program operations.
- Operations that require ROM Flash services are executed through an OpenSBI
  proxy in M-mode. The Linux MTD path does not duplicate private ROM calling
  conventions.

## XIP and external memory

- The cached Flash aperture is `[0x40000000, 0x50000000)`.
- The cached PSRAM aperture is `[0x50000000, 0x54000000)`.
- Linux executes XIP text from Flash and keeps writable runtime state in RAM.
- Before one boot stage hands cached memory to the next, it must satisfy the
  cache writeback, MMU, PMA/APM, and hart-local state contracts.
