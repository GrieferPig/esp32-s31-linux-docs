# Flash layout

The supplied image uses 16 MiB NOR flash. The offsets below are raw flash
offsets used when programming the chip.

| Offset | Capacity | Contents |
|---:|---:|---|
| `0x000000` | 8 KiB | Reserved before SPL |
| `0x002000` | 1016 KiB | `spl_app.bin` |
| `0x100000` | 2 MiB | `u-boot.itb` |
| `0x300000` | 64 KiB | `esp32s31_generic.dtb` |
| `0x310000` | 1984 KiB | `radio.sqfs` |
| `0x500000` | 6336 KiB | `xipImage` |
| `0xB30000` | 576 KiB | Persistent JFFS2 filesystem |
| `0xBC0000` | 64 KiB | HIL scratch partition |
| `0xBD0000` | 4288 KiB | `rootfs.sqfs` |

The HIL scratch partition is separate from persistent storage. See
[Configuration](../resources/configuration.md) for saved files and the writable
root filesystem.

## Raw offsets and mapped addresses

SPL maps raw flash offset `0x100000` to CPU address `0x40000000`.
For the partitions in that window:

- CPU address = `0x40000000` + raw flash offset − `0x100000`.
- The Linux flash node starts at `0x40000000`, so its partition offsets are
  relative to raw flash offset `0x100000`.

| Contents | Raw flash offset | CPU address | Linux partition offset |
|---|---:|---:|---:|
| Device tree | `0x300000` | `0x40200000` | `0x200000` |
| Kernel | `0x500000` | `0x40400000` | `0x400000` |
| Persistent storage | `0xB30000` | `0x40A30000` | `0xA30000` |

U-Boot's `booti` command uses the CPU addresses. Flashing commands use the raw
offsets. See [Boot process](../api-reference/system/boot-chain.md).

## Change the layout

The offsets and filenames are defined in
[`configs/esp32s31-layout.cfg`](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/configs/esp32s31-layout.cfg#L14-L39).
The image merge script checks each payload against its slot capacity. The
layout checker also compares the configuration with the Linux partitions and
shared memory definitions:

```sh
make check-layout
```

When moving a partition, update its users as well, including the device tree,
boot addresses and kernel XIP settings. The
[layout checker](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/check_s31_layout.py#L27-L64)
identifies the definitions that must agree.
