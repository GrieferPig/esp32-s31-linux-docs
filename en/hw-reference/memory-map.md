# Memory Map and DMA Reservations

## Major regions

| Region | Start | End/size | Owner and behavior |
|---|---:|---:|---|
| Cached PSRAM | `0x50000000` | 16 MiB | Linux writable memory and userspace |
| OpenSBI writable state | `0x2F00F000` | `0x2F018000` | OpenSBI data, stacks, and heap |
| Radio low heap | `0x2F018000` | `0x2F030000` | Secondary radio allocation pool |
| Radio main heap | `0x2F030000` | `0x2F071800` | Radio payload state and allocations |
| Radio exception area | `0x2F071800` | `0x2F072380` | Synchronous exception stack/guard |
| AXI GDMA descriptors | `0x2F072380` | 12 KiB | AXI DMA engine |
| AHB GDMA descriptors | `0x2F075380` | 4 KiB | AHB DMA engine |
| USB local state | `0x2F076380` | 64 B | USB driver reservation |
| Hart-1 mailbox | `0x2F0763A0` | implementation-sized | SMP startup/coordination |
| UART DMA | `0x2F076400` | 10 KiB | UART DMA rings |
| Radio high heap | `0x2F078C00` | `0x2F07CFB0` | Non-contiguous secondary radio pool |
| LP SRAM | `0x2E000000` | 32 KiB | LP firmware; final KiB is protocol control |

The canonical definitions live in `shared/s31_memory_layout.h`. Documentation
must describe ownership and constraints without copying historical debugging
notes from that header.

## DMA requirements

- Allocate streaming buffers through the Linux DMA API.
- Do not give a peripheral an arbitrary PSRAM virtual address.
- Descriptor rings that require internal SRAM use the reserved pools above.
- CPU and device ownership transitions require the appropriate map, sync, and
  unmap operations.
- The radio heaps are not general-purpose Linux memory.
- The LP control block at `0x2E007C00` is shared protocol state and must remain
  outside the LP firmware link region.

An overlay or driver that introduces a new fixed reservation must update the
shared header, device tree, and this reference together, with compile-time
adjacency checks where applicable.
