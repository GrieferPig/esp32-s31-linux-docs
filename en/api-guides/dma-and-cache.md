# DMA and cache

The S31 device tree declares SoC DMA non-coherent. Linux supplies cache writeback
and invalidation through vendor SBI calls, so drivers must transfer ownership
of PSRAM buffers between the CPU and DMA through the DMA API.
[Device-tree declaration](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L134-L144);
[cache operations](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/cache/esp32s31_cache.c#L111-L132).

This page is for driver development. Applications using interfaces such as SPI
and ALSA normally let those subsystems manage their DMA buffers.

## Descriptors and data buffers

The AHB and AXI GDMA drivers allocate hardware descriptors from reserved internal
SRAM. Client drivers provide the transfer data buffers through their subsystem
or DMA allocation and mapping APIs. A DMAengine client requests a prepared
transfer descriptor; it does not allocate or modify the GDMA hardware descriptor
pool directly. See [Memory map](../hw-reference/memory-map.md) for the reservations
and the [AHB](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/dma/esp32s31-ahb-gdma.c#L1006-L1017)
and [AXI](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/dma/esp32s31-axi-gdma.c#L1133-L1145)
pool initialization.

Keep the CPU pointer and the returned `dma_addr_t` separate. Give the DMA address
to DMAengine. For a streaming DMAengine mapping, obtain the mapping device with
`dmaengine_get_dma_device(chan)` and use that same device for mapping, checking
errors, synchronization and unmapping.
[DMAengine client contract](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/Documentation/driver-api/dmaengine/client.rst#L122-L140).

## Streaming buffer ownership

The mapping API and DMAengine use different direction constants:

| Transfer | DMA mapping direction | DMAengine direction |
| --- | --- | --- |
| Memory to peripheral | `DMA_TO_DEVICE` | `DMA_MEM_TO_DEV` |
| Peripheral to memory | `DMA_FROM_DEVICE` | `DMA_DEV_TO_MEM` |

For a receive buffer, the mapping fragment is:

```c
struct device *dma_dev = dmaengine_get_dma_device(chan);
dma_addr_t dma_addr;

dma_addr = dma_map_single(dma_dev, buffer, len, DMA_FROM_DEVICE);
if (dma_mapping_error(dma_dev, dma_addr))
    return -EIO;
```

Here `buffer` is a DMA-suitable kernel buffer, and `chan` is an acquired and
configured receive channel. After mapping, prepare and submit a descriptor with
`DMA_DEV_TO_MEM`, check submission errors, then issue the pending transfer. Keep
the buffer mapped and leave it untouched by the CPU while DMA owns it. Once the
transfer has finished, unmap it before the CPU reads or reuses the buffer:

```c
dma_unmap_single(dma_dev, dma_addr, len, DMA_FROM_DEVICE);
```

If the buffer stays mapped between transfers, use
`dma_sync_single_for_cpu()` after completion and before CPU access, then
`dma_sync_single_for_device()` after CPU access and before handing it back to
DMA. Preserve the mapping device, size and direction. An error before a transfer
starts still needs to release a successful mapping; an error after submission
also needs the termination sequence below.
[DMA mapping and unmapping](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/Documentation/core-api/dma-api-howto.rst#L522-L551);
[reusing a streaming mapping](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/Documentation/core-api/dma-api-howto.rst#L627-L653).

## Stop a transfer before releasing its resources

First stop new peripheral DMA requests and prevent new submissions on the channel.
In a context that may sleep, call `dmaengine_terminate_sync()` and check its return
value before unmapping or freeing buffers and callback state. This call waits for
the transfer and running completion callbacks; it must not run in atomic context
or in a completion callback on the same channel.

If termination begins in atomic context or a completion callback, use
`dmaengine_terminate_async()`, check its result, and arrange for a worker or other
sleepable context to call `dmaengine_synchronize()`. Release resources only after
synchronization. Do not call `dma_async_issue_pending()` between termination and
synchronization. These rules apply to timeout, removal and suspend paths as well
as ordinary transfer cleanup.
[Termination API and lifetime rules](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/include/linux/dmaengine.h#L1144-L1222).

## Examples in the port

The [SPI driver](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/spi/spi-esp32s31.c#L864-L879)
allocates private TX and RX buffers with `dma_alloc_noncoherent()`. Its target
transfer path synchronizes those buffers explicitly, rounds RX DMA length to a
multiple of four bytes, and terminates both channels during cleanup.
[Transfer setup](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/spi/spi-esp32s31.c#L205-L241);
[completion and cleanup](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/spi/spi-esp32s31.c#L350-L387).

The [I2S driver](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/sound/soc/espressif/esp32s31-i2s.c#L109-L115)
selects `SNDRV_DMA_TYPE_NONCOHERENT`; [ALSA's allocation layer](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/sound/core/memalloc.c#L860-L893)
provides the corresponding synchronization.

Sv32 has no uncached page-table attribute for these buffers. This is a page-table
limitation: the AXI GDMA driver separately maps a direct PSRAM alias for its own
recovery copies. Client drivers should follow their DMA API's ownership rules.
[Sv32 page-table definitions](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/include/asm/pgtable-32.h#L20-L29);
[AXI alias use](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/dma/esp32s31-axi-gdma.c#L528-L543).
