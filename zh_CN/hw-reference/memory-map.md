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
| 无线主区域 | `0x2F030000` | `0x2F071800` | 无线堆、缓冲区及 Wi-Fi 可执行 SRAM 子区 |
| 无线异常区域 | `0x2F071800` | `0x2F072380` | 异常栈和保护区域 |
| AXI GDMA 描述符 | `0x2F072380` | 12 KiB | DMA 描述符 |
| AHB GDMA 描述符 | `0x2F075380` | 4 KiB | DMA 描述符 |
| USB 与 hart-1 控制区 | `0x2F076380` | 64 字节 | hart-1 邮箱位于 `0x2F0763A0` |
| UART DMA | `0x2F076400` | 10 KiB | UART 缓冲区 |
| 无线高地址堆 | `0x2F078C00` | `0x2F07CFB0` | 额外的无线内存分配 |

HP 预留区域定义在
[`shared/s31_memory_layout.h`](https://github.com/GrieferPig/esp32-s31-linux/blob/main/shared/s31_memory_layout.h)
中。无线和 DMA 驱动直接使用这些区域。应用通过常规 Linux API 分配内存。


XIP 无线加载器还有以下地址约定，定义见内核的 `drivers/platform/esp32s31-radio-xip.h`：

| 映射或区域 | 地址/容量 | 用途 |
|---|---|---|
| 无线 Flash 虚拟基址 | `0xBE06E000` | 对应原始偏移 `0x06E000`、物理地址 `0x4006E000` |
| Wi-Fi 可执行 SRAM | 物理 `0x2F060000`，虚拟 `0xBE420000`；容量 `0x11800` | 从 Flash 复制的热点代码，位于上表无线主区域内 |
| 无线可写 arena | 内核符号 `esp32s31_radio_xip_ram`，40 KiB | PSRAM 中的初始数据与 BSS，地址取决于内核构建 |

无线 Flash 映射使用 4 MiB 对齐的 Sv32 页：虚拟 `[0xBE000000, 0xBE400000)` 对应物理 `[0x40000000, 0x40400000)`，1536 KiB 无线分区完全位于其中。启动映射覆盖从原始偏移零开始的完整 16 MiB Flash，Linux 从 `0x40400000` 执行。原始分区见[Flash 布局](flash-layout.md)。

无线堆必须排除正在使用的 Wi-Fi SRAM 代码，只能回收代码后的尾部，不能把整段可执行 SRAM 当作空闲堆。预链接工具会记录内核可写 arena 地址，因此无线镜像必须匹配内核构建。

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
