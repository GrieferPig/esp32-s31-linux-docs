# 系统架构

Linux 在 ESP32-S31 的两个高性能核上运行，并使用 Sv32 虚拟内存。项目提供的配置从映射的 Flash 执行内核代码，将 16 MiB PSRAM 用于可写数据和应用。

## 主要组件

| 组件 | 作用 |
|---|---|
| ROM 和 SPL | 启动芯片并初始化内存 |
| OpenSBI | 为 Linux 和 U-Boot 提供机器模式服务 |
| U-Boot | 携带设备树启动 Linux 镜像 |
| Linux | 运行应用，管理处理器、内存和设备 |
| Buildroot | 构建根文件系统和命令行工具 |
| 无线模块与载荷 | 提供 Wi-Fi 和 Bluetooth 运行时 |
| LP 固件 | 在低功耗核上执行邮箱和唤醒任务 |

启动依次经过 ROM、SPL、OpenSBI 和 U-Boot，随后 Linux 启动 BusyBox 用户空间。[启动流程](boot-chain.md)说明地址交接与启动服务。

## 内存与文件系统

就地执行（XIP）将内核代码保留在映射的 Flash 中，让 PSRAM 用于可写数据与应用。内部 SRAM 存放固件数据、无线分配区和 DMA 描述符。具体区域与归属见[内存映射](../../hw-reference/memory-map.md)。

根文件系统使用 SquashFS 镜像及以 JFFS2 为后端的可写覆盖层。重启后保留的内容、软件包管理文件的替换和临时存储见[配置](../../resources/configuration.md)。

## 外设

应用通过 GPIO 字符设备、I2C、SPI、ALSA 和套接字等 Linux 接口访问硬件。`s31-overlay` 启用可选外设并选择其引脚。大多数外设示例需要完整外设[构建配置](../../get-started/build-profiles.md)。

## 无线与低功耗核

Wi-Fi 和 Bluetooth 共享 Linux 无线模块与载荷。无线服务工作线程运行在 HP 核 0；Wi-Fi 前端接收 NAPI 和缓冲区补充工作运行在 HP 核 1。载荷兼容任务保留其请求的亲和性。[中断与 SMP 参考](interrupts-smp.md)解释这些执行位置及 IRQ 路由边界。Bluetooth 通常通过 `/dev/s31-hci` 使用 BTstack。

LP 固件由 Linux remoteproc 加载，处理邮箱、定时器和 GPIO 唤醒请求。它们各自的接口见[无线参考](../radio/index.md)及 [LP 参考](../lp-core/index.md)。
