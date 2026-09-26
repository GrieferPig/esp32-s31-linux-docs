# Flash layout

The image uses 16 MiB NOR flash. Firmware, radio files, saved settings, and
the root filesystem occupy separate regions.

| Offset | Capacity | Contents |
|---:|---:|---|
| `0x000000` | 8 KiB | Reserved before SPL |
| `0x002000` | 1016 KiB | `spl_app.bin` |
| `0x100000` | 2 MiB | `u-boot.itb` |
| `0x300000` | 64 KiB | `esp32s31_generic.dtb` |
| `0x310000` | 1984 KiB | `radio.sqfs` |
| `0x500000` | 6336 KiB | `xipImage` |
| `0xB30000` | 640 KiB | Persistent JFFS2 filesystem |
| `0xBD0000` | 4288 KiB | `rootfs.sqfs` |

U-Boot uses mapped addresses when starting
Linux. See [Boot process](../api-reference/system/boot-chain.md).

## Change the layout

The offsets and filenames are defined in
[`configs/esp32s31-layout.cfg`](https://github.com/GrieferPig/esp32-s31-linux/blob/main/configs/esp32s31-layout.cfg).
The merge script checks that each file fits its region.

TODO: auto infer component layout from the cfg
