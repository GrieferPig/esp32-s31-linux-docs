# DMA and cache

The ESP32-S31 uses non-coherent DMA. When a peripheral accesses a PSRAM buffer,
the CPU cache needs to be synchronized so the CPU and peripheral see the
latest data.

This page is for driver development. Applications normally let their Linux
subsystem handle DMA buffers.

## Allocate descriptors and data separately

The AHB and AXI GDMA drivers store descriptors in reserved internal SRAM.
Transfer data uses the buffer allocation and mapping path selected by the
client driver.

Use DMAengine's descriptor support and the device's DMA API. The returned DMA
address is the address to give to the engine; keep the CPU pointer for CPU
access. The descriptor reservations are listed in
[Memory map](../hw-reference/memory-map.md).

## Transfer a streaming buffer

A typical streaming transfer follows this sequence:

1. Prepare the buffer and map it for the transfer direction. Check for a
   mapping error before submitting the transfer.
2. Submit the descriptor and let DMA use the buffer until completion.
3. Synchronize the buffer for CPU access, or unmap it, before reading received
   data or reusing the storage.

For a buffer that remains mapped between transfers, use
`dma_sync_single_for_device()` before the device uses it and
`dma_sync_single_for_cpu()` before the CPU accesses it again. Use the direction
and size required by the mapping.

## Examples in the port

The [SPI driver](https://github.com/GrieferPig/linux-esp32-s31/blob/7b593bfc0c01d117410dead80868301c3e380fec/drivers/spi/spi-esp32s31.c)
uses private DMA buffers with explicit synchronization. It also handles RX
alignment and terminates DMA during transfer cleanup.

The [I2S driver](https://github.com/GrieferPig/linux-esp32-s31/blob/7b593bfc0c01d117410dead80868301c3e380fec/sound/soc/espressif/esp32s31-i2s.c)
uses `SNDRV_DMA_TYPE_NONCOHERENT`, allowing ALSA to synchronize PCM buffers.
Sv32 has no uncached page-table attribute for making these PSRAM buffers
coherent.

## Stop a transfer

On an error, stop the peripheral and terminate the DMA channel before freeing
or reusing its buffers. This also applies when removing a driver or suspending
a device.
