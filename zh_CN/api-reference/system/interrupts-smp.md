# 中断与 SMP

每个 HP 核都有一个 CLIC。Linux 在各核启动时初始化本地中断状态，并为 SYSTIMER 事件和 IPI 门铃使用不同的保留槽位。矩阵中断源与 CLIC 槽位的具体分配见[中断路由](../../hw-reference/interrupt-routing.md)。

## CPU 亲和性

**当前通用外设中断固定在 HP 核 0 上。** 矩阵 irqchip 只接受包含 CPU 0 的亲和性掩码，并将实际亲和性报告为 CPU 0。仅指定 CPU 1 会返回 `-EINVAL`；普通的 IRQ 亲和性写操作不能将这些处理函数迁移到 HP 核 1。本地定时器和 IPI 路由通过独立的每核流程配置。参见 [`esp_intmtx_set_affinity()`](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/irqchip/irq-esp-intmtx.c)。

无线通用 IRQ 和公共工作线程使用 HP 核 0；仅 Wi-Fi 的 SoftMAC 模式使用原生任务服务，不启动公共无线工作线程。前端将接收 NAPI 和 I/O 工作定向到 HP 核 1；核 1 不在线时回退到 HP 核 0。兼容任务保留请求的亲和性，无固定亲和性的任务可以迁移。参见[无线工作线程](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/platform/esp32s31-radio-smode.c)、[任务绑定](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/platform/esp32s31-radio-rtos.c)及[前端接收工作](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/net/wireless/espressif/esp32s31_softmac.c)。

## 查看中断活动

```sh
cat /sys/devices/system/cpu/online
cat /proc/interrupts
```

`/proc/interrupts` 显示各在线 CPU 的计数。排查完成事件缺失或负载异常时，可比较外设操作前后的计数。通用设备计数集中在 CPU 0 上符合当前路由策略，单凭这一现象不能判定 SMP 故障。

## 编写中断处理函数

通过 `platform_get_irq()` 获取 Linux IRQ，再通过 Linux IRQ API 注册处理函数。读取外设状态，处理已触发的中断源，并按该设备的要求确认中断。对于共享或复用的中断源，应先查看状态，确定事件是否属于该驱动。

硬中断中的工作应有明确的执行上限且不可睡眠。子系统允许时，将处理推迟到线程化处理函数、工作线程或 NAPI。通过合适的内核同步机制保护与其他 CPU 或上下文共享的数据；IRQ 仅路由到 CPU 0 不意味着驱动的其他部分是单线程的。[I2C IRQ 注册](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/i2c/busses/i2c-esp32s31.c)是一个具体的平台驱动示例。

## DMA 完成

AHB 和 AXI GDMA 提供者处理硬件完成中断，并通过 DMAengine 回调通知客户端。回调必须遵守其执行上下文的限制，释放缓冲区前必须同步完成终止操作。参见 [DMA 与缓存一致性](../../api-guides/dma-and-cache.md)。
