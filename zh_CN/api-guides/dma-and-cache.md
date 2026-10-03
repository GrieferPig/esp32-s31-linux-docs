# DMA 与缓存

S31 的设备树将 SoC DMA 声明为非一致性 DMA。Linux 通过厂商 SBI 调用执行缓存写回和失效操作，因此驱动必须使用 DMA API，在 CPU 与 DMA 之间交接 PSRAM 缓冲区的访问权。
[设备树声明](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/boot/dts/espressif/esp32s31.dtsi)；[缓存操作](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/cache/esp32s31_cache.c)。

本页面向驱动开发。使用 SPI、ALSA 等接口的应用，通常由相应子系统管理 DMA 缓冲区。

## 描述符与数据缓冲区

AHB 和 AXI GDMA 驱动从预留的内部 SRAM 中分配硬件描述符。客户端驱动通过所属子系统或 DMA 分配、映射 API 提供传输数据缓冲区。DMAengine 客户端请求准备好的传输描述符，不直接分配或修改 GDMA 的硬件描述符池。预留区域见[内存映射](../hw-reference/memory-map.md)；描述符池的初始化见 [AHB 驱动](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/dma/esp32s31-ahb-gdma.c)和 [AXI 驱动](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/dma/esp32s31-axi-gdma.c)。

分别保存 CPU 指针和返回的 `dma_addr_t`，将 DMA 地址交给 DMAengine。为 DMAengine 建立流式映射时，先通过 `dmaengine_get_dma_device(chan)` 获取用于映射的设备；映射、错误检查、同步和解除映射必须使用同一个设备。
[DMAengine 客户端约定](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/Documentation/driver-api/dmaengine/client.rst)。

## 流式缓冲区的访问权

映射 API 与 DMAengine 使用不同的方向常量：

| 传输方向 | DMA 映射方向 | DMAengine 方向 |
| --- | --- | --- |
| 内存到外设 | `DMA_TO_DEVICE` | `DMA_MEM_TO_DEV` |
| 外设到内存 | `DMA_FROM_DEVICE` | `DMA_DEV_TO_MEM` |

接收缓冲区的映射代码片段如下：

```c
struct device *dma_dev = dmaengine_get_dma_device(chan);
dma_addr_t dma_addr;

dma_addr = dma_map_single(dma_dev, buffer, len, DMA_FROM_DEVICE);
if (dma_mapping_error(dma_dev, dma_addr))
    return -EIO;
```

其中，`buffer` 是适用于 DMA 的内核缓冲区，`chan` 是已获取并配置好的接收通道。完成映射后，以 `DMA_DEV_TO_MEM` 方向准备并提交描述符，检查提交错误，然后启动待处理的传输。DMA 持有缓冲区访问权期间，保持映射，并避免 CPU 访问该缓冲区。传输完成后，在 CPU 读取或复用缓冲区前解除映射：

```c
dma_unmap_single(dma_dev, dma_addr, len, DMA_FROM_DEVICE);
```

如果缓冲区在多次传输之间保持映射，应在传输完成后、CPU 访问前调用 `dma_sync_single_for_cpu()`；CPU 访问结束后，在将缓冲区重新交给 DMA 前调用 `dma_sync_single_for_device()`。映射所用的设备、大小和方向应保持一致。即使在启动传输前出错，也需要释放已经成功建立的映射；如果在提交之后出错，还需要执行下一节的终止流程。
[DMA 映射与解除映射](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/Documentation/core-api/dma-api-howto.rst)；[复用流式映射](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/Documentation/core-api/dma-api-howto.rst)。

## 释放资源前终止传输

先停止外设发出新的 DMA 请求，并阻止向通道提交新传输。在允许睡眠的上下文中，调用 `dmaengine_terminate_sync()` 并检查返回值，然后再解除映射或释放缓冲区、回调状态。该调用会等待传输和正在运行的完成回调结束；不能在原子上下文中调用，也不能在同一通道的完成回调中调用。

如果需要从原子上下文或完成回调中发起终止，调用 `dmaengine_terminate_async()` 并检查结果，再安排工作线程或其他允许睡眠的上下文调用 `dmaengine_synchronize()`。同步完成后才能释放资源。在终止与同步之间，不要调用 `dma_async_issue_pending()`。这些规则也适用于超时、驱动移除和设备挂起路径。
[终止 API 与资源生命周期规则](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/include/linux/dmaengine.h)。

## 本移植项目中的示例

[SPI 驱动](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/spi/spi-esp32s31.c)使用 `dma_alloc_noncoherent()` 分配私有 TX、RX 缓冲区。其目标设备传输路径显式同步缓冲区，将 RX DMA 长度向上对齐到四字节的倍数，并在清理时终止两个通道。
[传输准备](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/spi/spi-esp32s31.c)；[完成与清理](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/spi/spi-esp32s31.c)。

[I2S 驱动](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/sound/soc/espressif/esp32s31-i2s.c)选择 `SNDRV_DMA_TYPE_NONCOHERENT`，由 [ALSA 分配层](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/sound/core/memalloc.c)提供相应的同步操作。

Sv32 没有可将这些缓冲区设为非缓存的页表属性。这一限制针对页表：AXI GDMA 驱动另行映射了 PSRAM 的直通别名，用于自身的恢复复制。客户端驱动应遵守所用 DMA API 的访问权规则。
[Sv32 页表定义](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/include/asm/pgtable-32.h)；[AXI 别名的使用](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/dma/esp32s31-axi-gdma.c)。
