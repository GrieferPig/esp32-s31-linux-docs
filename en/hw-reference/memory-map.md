# Memory and DMA

## Capacity and address space

| Region | Address | Capacity or limit | Access |
| --- | --- | ---: | --- |
| CPU subsystem | `[0x00000000, 0x20000000)` | 512 MiB aperture | Target-dependent HP/LP access |
| CPU peripherals | `[0x2C000000, 0x2C020000)` | 128 KiB | Register window |
| Debug peripherals | `[0x2D000000, 0x2D008000)` | 32 KiB | Debug domain |
| LP SRAM | `[0x2E000000, 0x2E008000)` | 32 KiB | HP/LP shared and retention-capable |
| HP SRAM | `[0x2F000000, 0x2F080000)` | 512 KiB | Internal HP SRAM |
| ROM | `[0x2F800000, 0x2F850000)` | 320 KiB | HP access through the ROM cache |
| Cached Flash | `[0x40000000, 0x50000000)` | 256 MiB maximum | Read and XIP |
| Cached PSRAM | `[0x50000000, 0x54000000)` | 64 MiB maximum | Shared write-back data cache |
| Direct Flash | `[0xA0000000, 0xB0000000)` | 256 MiB maximum | Cache bypass |
| Direct PSRAM | `[0xC0000000, 0xC4000000)` | 64 MiB maximum | Cache bypass |

The current module provides 16 MiB of Flash and 16 MiB of PSRAM. Normal drivers
must not allocate or map unlisted apertures on their own.

## Caches and MMUs

- Each HP hart has a private 32 KiB L1 instruction cache.
- Both HP harts share a 64 KiB L1 data cache with write-through and write-back
  support.
- An Espressif MMU manages Flash and PSRAM mappings. The Linux virtual-memory
  layer uses the Sv32 MMU.
- Software must perform direction-appropriate cache maintenance when mixing
  cached and direct aliases, handing memory between boot stages, or using
  non-coherent DMA.
- The S31 Sv32 page-table walker does not snoop the shared write-back data
  cache. Page-table writes must be written back before the first `satp` load.
- Before hart1 uses cached PSRAM, its instruction-cache bus, PMA, and access
  permissions must be configured locally. Shared MMU and cache setup does not
  replace hart-local PMA state.

## Memory protection

- PMP controls a hart's physical-memory access permissions.
- APM controls master access to ROM, HP memory, and HP/LP peripherals.
- APM can select security modes for masters such as DMA engines and can apply
  permissions to address ranges and individual registers.
- The PMA, PMP, APM, and MSPI PMS state established during boot is a prerequisite
  for Linux access to Flash, PSRAM, and peripherals.

## DMA placement rules

- Descriptor rings and linked-list nodes must reside in DMA-visible internal
  HP SRAM.
- A PSRAM address must not be used as descriptor metadata or a descriptor link.
- Payload buffers are managed independently from descriptors. A payload may
  reside in PSRAM when the device's addressing and cache requirements permit it.
- Drivers must program the DMA address returned by the DMA mapping API, not a
  cached CPU virtual address.
- Cached payloads require synchronization in the transfer direction. The
  console UHCI path uses an internal-SRAM payload buffer as a device-specific
  reliability constraint; this does not change the general DMA rules.

## Current internal-SRAM reservations

The following ranges use half-open notation:

| Range | Owner |
| --- | --- |
| `[0x2F030000, 0x2F071800)` | Radio blob heap |
| `[0x2F071800, 0x2F072380)` | Radio synchronous-exception stack |
| `[0x2F072380, 0x2F075380)` | AXI-GDMA descriptors |
| `[0x2F075380, 0x2F076380)` | AHB-GDMA descriptors |
| `[0x2F076380, 0x2F0763C0)` | USB local SRAM |
| `[0x2F0763C0, 0x2F076400)` | Alignment padding |
| `[0x2F076400, 0x2F078C00)` | UHCI0 UART DMA payload |

Adding a DMA client requires a corresponding descriptor reservation in the
factory application's reserved-memory registration. Descriptor capacity and
payload-buffer allocation must be accounted for separately.
