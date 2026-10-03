# Flash layout

The image uses all 16 MiB of NOR flash with no gaps between regions. The first
8 KiB is the mandatory ROM FlashEncryption reservation; every remaining byte
belongs to one of the slots below. Range ends are exclusive.

| Raw start | Raw end | Capacity | Contents |
|---:|---:|---:|---|
| `0x000000` | `0x002000` | 8 KiB | Reserved for ROM FlashEncryption metadata |
| `0x002000` | `0x00E000` | 48 KiB | `spl_app.bin` |
| `0x00E000` | `0x05E000` | 320 KiB | `u-boot.itb` |
| `0x05E000` | `0x06E000` | 64 KiB | `esp32s31_generic.dtb` |
| `0x06E000` | `0x1EE000` | 1536 KiB | `radio.bin`: prelinked radio XIP payload |
| `0x1EE000` | `0x400000` | 2120 KiB | Persistent JFFS2 filesystem |
| `0x400000` | `0xA00000` | 6144 KiB | `xipImage` |
| `0xA00000` | `0x1000000` | 6144 KiB | `rootfs.sqfs` |

Persist fills the space between radio and Linux. There is no separate HIL
scratch partition. The seven child MTD partitions are read-only except persist.
`CONFIG_MTD_PARTITIONED_MASTER=y` intentionally also exposes the writable
`40000000.flash` master device covering all 16 MiB. Master access bypasses the
child partitions' read-only flags and includes the reserved prefix and boot
slots; callers must account for those ranges when performing raw operations.
Persist/rootfs are found by label, not by fixed MTD device numbers.

The same whole-flash master is continuously readable from offset 0 through
`0xFFFFFF`. Linux supplies its normal `/dev/mtdN` character node and a
read-only `/dev/mtdNro` alias; identify `N` from the sysfs name
`40000000.flash` rather than assuming its number. Reading the read-only alias
covers the complete 16 MiB, including the reserved prefix and every partition,
without granting write access through that alias. With `CONFIG_MTD_BLOCK=y`,
`/dev/mtdblockN` also exposes the complete master as a block device. The writable
master remains available as requested.

## Raw offsets and XIP addresses

The boot mapping covers raw flash `[0x000000, 0x1000000)` linearly at physical
`[0x40000000, 0x41000000)`. Therefore the FIT is at `0x4000E000`, OpenSBI's
XIP payload starts at `0x4000E400`, the Linux DTB is at `0x4005E000`, and Linux
starts at `0x40400000`.

The Linux start is aligned to a 4 MiB Sv32 megapage. This matters for kernels
larger than 4 MiB: an unaligned XIP start can reach the page-table `BUG_ON`
described in [issue #1](https://github.com/GrieferPig/esp32-s31-linux/issues/1).
Do not move Linux merely to close a gap; persist already fills the space up
to the required boundary.

The radio slot starts at physical `0x4006E000` and virtual `0xBE06E000`, inside
the aligned 4 MiB leaf mapping from virtual `0xBE000000` to physical
`0x40000000`. See [Memory map](memory-map.md) and
[Boot process](../api-reference/system/boot-chain.md).

## Change the layout

The offsets and filenames are defined in
[`configs/esp32s31-layout.cfg`](https://github.com/GrieferPig/esp32-s31-linux/blob/main/configs/esp32s31-layout.cfg).
The merge script checks that each file fits its region, including the 48 KiB
SPL limit. Coordinate changes with the bootloader, OpenSBI, kernel XIP and
radio mappings, device-tree partitions, image tooling, and flashing commands.

Run `python3 tools/checks/layout.py` from the parent repository to check the
shared flash and SRAM contracts. To read a slot capacity in bytes, use, for
example, `python3 tools/checks/layout.py --size PERSIST`.

The radio XIP image is linked against the kernel and must be updated with its
matching kernel/module. The Linux radio module lives in `rootfs.sqfs`.

## Preserve data

Slot-wise `make flash-all` leaves persist untouched **only when the board
already uses this layout**. Writing the contiguous `s31_full_flash.bin`
overwrites persist, even without a separate chip erase.

Whenever changing the installed layout, back up needed files and settings to
another device, verify the backup, perform a clean installation, then restore
the needed files/settings. See
[Flash and first boot](../get-started/flash-and-first-boot.md).

Hardware boot and flashing validation of this compact layout is still pending.
Host layout checks alone do not establish a working hardware boot.
