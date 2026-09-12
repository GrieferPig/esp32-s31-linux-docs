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

## Cache service and writable Flash

Linux serializes the shared external-cache engine and calls the OpenSBI vendor
cache service. The S31 ROM operates on 64-byte cache lines; OpenSBI expands a
valid physical range to cover every touched line before calling the ROM and
returns ROM failures through the SBI result. DMA callers must still follow the
ownership rules above: expanding a range does not make an adjacent dirty CPU
buffer safe to invalidate.

The Flash MTD driver serializes reads, writes, and erases. A program or erase
completes its D-cache and I-cache invalidation before a reader can acquire the
MTD lock. Failed cache maintenance is reported as an MTD I/O error rather than
counted as a successful write. This matters for JFFS2 garbage collection,
which must see the programmed nodes and the current erased-block contents.

The M-mode ROM Flash proxy executes its complete critical section from SRAM.
Before acknowledging its SRAM park, the peer saves and disables its branch
predictor. The caller saves and disables its own predictor before stalling the
peer, writes back dirty PSRAM, suspends both instruction caches and the shared
data cache, then disables Flash auto-suspend and runs the legacy ROM
program/erase call. It restores auto-suspend and cache autoload state
before releasing the peer. Each hart restores only the predictor bits that
were enabled on entry, including error paths. Parking CPUs alone does not
quiesce cache prefetch;
the SPI0 cache read path must also stop while SPI1 uses this ROM interface.

The peer's wait loop and all handshake words are in OpenSBI's uncached SRAM.
The Linux IPI callback enters that loop through the Flash SBI extension; it
carries no caller-stack pointer. A PSRAM atomic polling loop is unsafe at this
boundary because stopping its CPU can stop an external-cache transaction.
The preparing CPU keeps IRQs enabled and uses the existing S31 IRQ polling
fallback while waiting for the peer, so pending remote TLB work can progress.
