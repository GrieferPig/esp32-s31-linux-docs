# DMA and Cache

Use the Linux DMA API for payload buffers and the S31 DMAengine providers for
transfers. Allocate descriptors from the device's declared reserved pool when
the controller cannot address ordinary PSRAM coherently.

For streaming mappings, map before device ownership, synchronize at every
CPU/device transition when required, and unmap after completion. For coherent
allocations, still obey the device's addressing and internal-SRAM limits.

Do not translate an arbitrary virtual pointer to a bus address, assume cached
PSRAM is coherent, reuse radio-owned pools, or free a ring while its IRQ/DMA
channel can still complete. Error and remove paths must terminate channels,
mask IRQs, reclaim descriptors, and release provider references in order.
