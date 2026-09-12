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
| `0xBC0000` | HIL scratch | 64 KiB reserved for explicit HIL flash tests |
| `0xBD0000` | `rootfs.sqfs` | Read-only Linux root filesystem |
| `0x1000000` | end of flash | End of the 16 MiB address space |

Normal full-image generation has no `persist.jffs2` payload. `make flash-all`
and individual slot updates skip the persistent address range. Writing the
contiguous `s31_full_flash.bin` from offset zero still programs the `0xff`
padding across that range and therefore does not preserve existing persist
data; back it up first or use the slot-wise targets. The canonical values are
maintained in `configs/esp32s31-layout.cfg` in the parent repository.

## Filesystem behavior

The root filesystem is immutable SquashFS. Persistent state is mounted from
JFFS2 and overlaid or bind-mounted by early userspace where configured. The
radio image is separate so payload licensing and update policy do not become
implicit properties of the root filesystem.

Persist occupies 576 KiB from `0xB30000` to `0xBC0000`; HIL scratch is
a separate 64 KiB partition. Slot-wise updates preserve both.

## Writable Flash SBI compatibility

The port-specific Flash extension is `0x09000000`. Update the matched SPL/FIT,
Linux kernel, and rootfs as separate slots while preserving persist. A new
kernel checks the SRAM park preparation call before queuing a peer callback;
an older OpenSBI which lacks it returns an error and cannot silently perform
a Flash write through the unsafe handshake. The matching OpenSBI refuses ROM
writes and erases unless the other hart has entered its SRAM park loop.

| Function | ID | Inputs | Successful result |
| --- | --- | --- | --- |
| Program | 0 | raw address, aligned PSRAM buffer, length up to 32 bytes | ROM result zero |
| Erase | 1 | raw address, sector-aligned length | ROM result zero |
| Prepare | 2 | other hart ID | Zero; initializes SRAM state |
| Park | 3 | none; runs on the target hart | Zero after release |
| Status | 4 | other hart ID | Bit 0 entered, bit 1 exited |
| Release | 5 | other hart ID, callback queued (0 or 1) | Zero |

The Linux caller pins its CPU, prepares the peer, queues one native IPI
callback, and waits for entered before programming or erasing. Both peer
instructions and state words live in uncached internal SRAM. The ROM guard
disables both harts' branch predictors before stalling the peer, writes back
dirty PSRAM, suspends the external caches, and restores caches before
unstalling it. Release completes the SRAM wait, and each hart restores its
previous predictor enable bits.

If the IPI queue call failed, release with queued=0 cancels the preparation.
If a queued callback has not entered yet, release lets it exit immediately
when it arrives. Preparation rejects reuse until that callback publishes its
exit; a delayed callback never dereferences a returned caller-stack object.
Writes require both Linux CPUs online. CPU hotplug during writable Flash is
outside the current support boundary.
