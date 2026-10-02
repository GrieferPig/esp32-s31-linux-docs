# 内存映射

项目提供的配置使用以下内存区域：

- 外部 PSRAM（提供的镜像使用 16 MiB）
- 内部 HP SRAM（512 KiB）
- 内部 LP SRAM（32 KiB）

Linux 使用外部 PSRAM 存放可写内核数据和应用。内部 HP SRAM 存放固件、
无线内存分配和 DMA 缓冲区。

## HP 内存

下表中的结束地址不包含在范围内。详细映射见
[ESP32-S31 技术参考手册](https://documentation.espressif.com/esp32-s31_technical_reference_manual_en.pdf)。

| 区域 | 起始地址 | 结束地址或大小 | 用途 |
|---|---:|---:|---|
| PSRAM | `0x50000000` | 16 MiB | Linux 数据和应用 |
| OpenSBI 数据 | `0x2F00F000` | `0x2F018000` | 数据、栈和堆 |
| 无线低地址堆 | `0x2F018000` | `0x2F030000` | 无线内存分配 |
| 无线主区域 | `0x2F030000` | `0x2F071800` | 无线数据和内存分配 |
| 无线异常区域 | `0x2F071800` | `0x2F072380` | 异常栈和保护区域 |
| AXI GDMA 描述符 | `0x2F072380` | 12 KiB | DMA 描述符 |
| AHB GDMA 描述符 | `0x2F075380` | 4 KiB | DMA 描述符 |
| USB/状态保留区域 | `0x2F076380` | 64 字节 | 保留的共享 SRAM |
| UART DMA | `0x2F076400` | 10 KiB | UART 缓冲区 |
| 无线高地址堆 | `0x2F078C00` | `0x2F07CFB0` | 额外的无线内存分配 |

HP 预留区域定义在
[`shared/s31_memory_layout.h`](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/shared/s31_memory_layout.h)
中。无线和 DMA 驱动直接使用这些区域。应用通过常规 Linux API 分配内存。

## LP 内存

| 区域 | 地址 | 大小 |
|---|---:|---:|
| LP SRAM | `0x2E000000` | 总计 32 KiB |
| OpenSBI 挂起快照 | `0x2E002000` | 占用 LP SRAM 中的 20 KiB |
| 休眠控制预留区域 | `0x2E007C00` | LP SRAM 的最后 1 KiB |

LP 固件构建使用最前面的 8 KiB，结束地址为 `0x2E002000`。安排 LP 固件代码、
数据和栈的位置时，请避开快照和控制区域。休眠控制
结构体本身为 112 字节，较大的预留区域为其周围留出了余量。

构建和加载 LP 代码的方法见[LP 固件开发](../api-guides/lp-firmware-development.md)。

## DMA 缓冲区

DMA 描述符使用上述预留 SRAM 区域。传输缓冲区使用对应 Linux 驱动提供的
分配和映射 API。在 ESP32-S31 上，CPU 与 DMA 引擎共享 PSRAM 缓冲区时
需要同步缓存。

驱动示例见[DMA 和缓存](../api-guides/dma-and-cache.md)。
