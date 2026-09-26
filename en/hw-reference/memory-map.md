# Memory map

S31 consists of three main memory regions:

- external PSRAM (16MiB typical, max 64 MiB, depending on the board)
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
| Radio main area | `0x2F030000` | `0x2F071800` | Radio data and allocations |
| Radio exception area | `0x2F071800` | `0x2F072380` | Exception stack and guards |
| AXI GDMA descriptors | `0x2F072380` | 12 KiB | DMA descriptors |
| AHB GDMA descriptors | `0x2F075380` | 4 KiB | DMA descriptors |
| USB and hart-1 control | `0x2F076380` | 64 bytes | Shared control area; hart-1 mailbox at `0x2F0763A0` |
| UART DMA | `0x2F076400` | 10 KiB | UART buffers |
| Radio high heap | `0x2F078C00` | `0x2F07CFB0` | Additional radio allocations |

The HP reservations are defined in
[`shared/s31_memory_layout.h`](https://github.com/GrieferPig/esp32-s31-linux/blob/main/shared/s31_memory_layout.h).
The radio and DMA drivers use these areas directly. Applications allocate
memory through the usual Linux APIs.

## LP memory

| Region | Address | Size |
|---|---:|---:|
| LP SRAM | `0x2E000000` | 32 KiB total |
| OpenSBI suspend snapshot | `0x2E002000` | 20 KiB within LP SRAM |
| Sleep-control reservation | `0x2E007C00` | Final 1 KiB of LP SRAM |

Keep the snapshot and control regions free when placing LP firmware data and
stacks. The sleep-control structure itself is 112 bytes; the larger reservation
leaves room around it.

See [LP firmware development](../api-guides/lp-firmware-development.md) for
building and loading LP code.

## DMA buffers

DMA descriptors use the reserved SRAM regions above. Transfer buffers use
the allocation and mapping APIs provided by the corresponding Linux driver.
The ESP32-S31 needs cache synchronization when the CPU and a DMA engine share
PSRAM buffers.

For driver examples, see [DMA and cache](../api-guides/dma-and-cache.md).
