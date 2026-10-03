# Memory map

The supplied configuration uses these memory regions:

- external PSRAM (16 MiB in the supplied image)
- internal HP SRAM (512 KiB)
- internal LP SRAM (32 KiB)

Linux uses external PSRAM for writable kernel data and applications. Internal
HP SRAM holds firmware, radio allocations, and DMA buffers.

## HP memory

Range ends in this table are exclusive. For a detailed map, see [ESP32-S31 Technical Reference Manual](https://documentation.espressif.com/esp32-s31_technical_reference_manual_en.pdf).

| Region | Start | End or size | Use |
|---|---:|---:|---|
| PSRAM | `0x50000000` | 16 MiB | Linux data and applications |
| OpenSBI data | `0x2F00F000` | `0x2F018000` | Data, stacks, and heap |
| Radio low heap | `0x2F018000` | `0x2F030000` | Radio allocations |
| Radio main area | `0x2F030000` | `0x2F071800` | Radio heap/buffers and the Wi-Fi executable SRAM subregion |
| Radio exception area | `0x2F071800` | `0x2F072380` | Exception stack and guards |
| AXI GDMA descriptors | `0x2F072380` | 12 KiB | DMA descriptors |
| AHB GDMA descriptors | `0x2F075380` | 4 KiB | DMA descriptors |
| USB/status reservation | `0x2F076380` | 64 bytes | Reserved shared SRAM |
| UART DMA | `0x2F076400` | 10 KiB | UART buffers |
| Radio high heap | `0x2F078C00` | `0x2F07CFB0` | Additional radio allocations |

The HP reservations are defined in
[`shared/s31_memory_layout.h`](https://github.com/GrieferPig/esp32-s31-linux/blob/main/shared/s31_memory_layout.h).
The radio and DMA drivers use these areas directly. Applications allocate
memory through the usual Linux APIs.

The XIP radio loader has additional address-space contracts in the kernel's
`drivers/platform/esp32s31-radio-xip.h`:

| Mapping or arena | Address/capacity | Purpose |
|---|---|---|
| Radio flash virtual base | `0xBE06E000` | Prelinked payload; raw flash `0x06E000`, physical `0x4006E000` |
| Wi-Fi executable SRAM | Physical `0x2F060000`, virtual `0xBE420000`; capacity `0x11800` | Hot code copied from the flash image; within the radio main area above |
| Radio writable arena | 40 KiB at kernel symbol `esp32s31_radio_xip_ram` | Initial data and BSS in kernel PSRAM; its address is build-dependent |

The radio flash mapping uses an aligned 4 MiB Sv32 leaf: virtual
`[0xBE000000, 0xBE400000)` maps physical `[0x40000000, 0x40400000)`.
The 1536 KiB payload slot fits inside that leaf. Boot maps the full 16 MiB of
flash from raw offset zero to physical `0x40000000`; Linux begins at the
4 MiB-aligned address `0x40400000`. See [Flash layout](flash-layout.md) for
all raw offsets and the alignment constraint.

The radio heap excludes the live Wi-Fi code bytes and may reclaim only the
tail after that code. Do not count the executable SRAM reservation as free
radio heap. The host prelinker records the kernel writable-arena address,
which is one reason the radio image must match the kernel build.

## LP memory

| Region | Address | Size |
|---|---:|---:|
| LP SRAM | `0x2E000000` | 32 KiB total |
| OpenSBI suspend snapshot | `0x2E002000` | 20 KiB within LP SRAM |
| Sleep-control reservation | `0x2E007C00` | Final 1 KiB of LP SRAM |

The LP firmware build reserves the first 8 KiB, ending at `0x2E002000`.
Keep the snapshot and control regions free when placing LP firmware code, data
and stacks. The sleep-control structure itself is 112 bytes; the larger reservation
leaves room around it.

See [LP firmware development](../api-guides/lp-firmware-development.md) for
building and loading LP code.

## DMA buffers

DMA descriptors use the reserved SRAM regions above. Transfer buffers use
the allocation and mapping APIs provided by the corresponding Linux driver.
The ESP32-S31 needs cache synchronization when the CPU and a DMA engine share
PSRAM buffers.

For driver examples, see [DMA and cache](../api-guides/dma-and-cache.md).
