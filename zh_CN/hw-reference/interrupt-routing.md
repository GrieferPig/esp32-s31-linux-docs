# 中断路由

中断矩阵将外设中断源路由到某个 HP 核的 CLIC 输入。这条路径中有三种编号：设备树中的**矩阵中断源**、分配的 **CLIC 槽位**和返回给驱动的 **Linux IRQ 编号**。它们属于不同的编号空间，不能将矩阵中断源编号直接当作 Linux IRQ。

## 保留的系统分配

| 所属模块 / 用途 | HP 核 | 矩阵中断源 | CLIC 槽位 | 分配用途 |
|---|---:|---:|---:|---|
| Linux IPI 门铃 | 0 | 65 | 40 | 每核软件中断 |
| Linux IPI 门铃 | 1 | 66 | 40 | 每核软件中断 |
| Linux SYSTIMER 事件 | 0 | 33 | 41 | 每核定时事件 |
| Linux SYSTIMER 事件 | 1 | 34 | 41 | 每核定时事件 |
| OpenSBI TIMERG0 定时器 1 | 0 | 26 | 48 | M 模式专用空闲唤醒保护 |
| OpenSBI TIMERG1 定时器 1 | 1 | 29 | 48 | M 模式专用空闲唤醒保护 |

Linux 通用外设分配器使用 CLIC 槽位 **16–47**，其中 40 和 41 保留给本地 IPI 和定时器路由。OpenSBI 使用的槽位 48 不属于这个分配池。两个核上的相同槽位编号代表不同的核本地输入。
参见[槽位常量](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/irqchip/irq-esp32s31-internal.h#L9-L12)、[本地中断源与配置](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/irqchip/irq-esp32s31-smp.c#L34-L42)、[分配器保留项](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/irqchip/irq-esp-intmtx.c#L298-L301)及 [OpenSBI 保护定时器定义](https://github.com/GrieferPig/opensbi-esp32-s31/blob/af2ff7c9c263bf474b0add45f614893e36d89814/platform/generic/espressif/esp32s31/services.c#L47-L85)。

两个 GPTimer 设备树节点都设置了 `espressif,reserved-timer-mask = <2>`。位 1 保留定时器 1，Linux counter 驱动会跳过该通道。保护定时器使用 40 MHz 晶振除以 40 的时钟，并设置 10,000 个计数周期的闹钟。
参见 [DTS 保留配置](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L1236-L1252)及使用它的 [GPTimer 驱动](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/counter/esp32s31-gptimer.c#L199-L211)。

无线运行时加载后，其使用的中断源归无线运行时管理；相应 Linux IRQ 通过平台中断路径申请。它们不是上表之外的固定 CLIC 槽位保留项。

## 外设与 GPIO 路由

外设的 `interrupts` 属性指定矩阵中断源及触发类型。Linux 选择 CLIC 槽位，并将 Linux IRQ 返回给驱动。当前通用外设路由指向 HP 核 0；具体亲和性限制与处理函数规则见[中断与 SMP](../api-reference/system/interrupts-smp.md)。

GPIO 信号路由通过 pinctrl 和覆盖文件路由设置单独配置。参见[覆盖文件目录](../resources/overlay-catalog.md)。
