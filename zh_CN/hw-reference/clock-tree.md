# 时钟树

Linux 时钟提供者通过公共时钟框架（CCF）导出根时钟、部分父时钟关系、分频器及外设控制。下表描述该提供者的注册项及频率计算。

## 已注册的父时钟与分频关系

| 时钟 | 已注册的父时钟 | 提供者中的频率关系 |
|---|---|---|
| `xtal` | 无 | 从配置读取晶振频率；回退值为 40 MHz |
| `rc-fast`、`rc-slow`、`xtal32k` | 无 | 固定的模型频率：17.5 MHz、136 kHz、32.768 kHz |
| `cpll`、`mpll`、`apll` | `xtal` | 根据分频寄存器计算 PLL 频率；APLL 还包含小数部分配置 |
| `bbpll` | `xtal` | 固定的模型频率 480 MHz |
| `pll-f20`、`pll-f60`、`pll-f80`、`pll-f120`、`pll-f160`、`pll-f240` | `bbpll` | 父时钟频率除以已配置的分频值 |
| `pll-f25` | `mpll` | 父时钟频率除以已配置的分频值 |
| `pll-f50` | `cpll` 或 `mpll` | 选中的父时钟除以已配置的分频值 |
| `xtal-d2` | `xtal` | 固定的模型频率 20 MHz |
| `cpu` | `xtal`、`cpll`、`rc-fast` 或 `pll-f240` | 选中的父时钟除以 CPU 分频值 |
| `mem` | `cpu` | CPU 频率除以 1 或 2 |
| `sys` | `cpu` | CPU 频率除以系统分频值 |
| `apb` | `sys` | 系统频率除以 APB 分频值 |
| `emac-rgmii-txc` | `mpll` | 可编程的发送时钟分频器 |

参见[父时钟定义](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L1382-L1390)、[时钟注册](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L1485-L1632)及[频率计算](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L910-L962)。
许多外设时钟以固定频率或初始总线频率单独注册，没有 CCF 父时钟关系。

## CPU 工作频点

两个 HP 核共用 `cpu` 时钟及同一张 OPP 表。项目提供的设备树公开 80、160、240 和 320 MHz。时钟驱动配置以下时钟源与分频组合：`mem` 和 `sys` 对 CPU 时钟分频，`apb` 对 `sys` 分频。

| CPU 频率 | 时钟源 | CPU 分频值 | 内存分频值 | 系统分频值 | APB 分频值 |
|---|---|---:|---:|---:|---:|
| 80 MHz | `cpll` | 4 | 1 | 1 | 2 |
| 160 MHz | `cpll` | 2 | 1 | 2 | 2 |
| 240 MHz | `pll-f240` | 1 | 2 | 3 | 2 |
| 320 MHz | `cpll` | 1 | 2 | 3 | 2 |

驱动还提供用于关机交接的 40 MHz XTAL 配置；它不属于项目 CPU 表公开的 OPP。时钟源选择与分频器的更新会一起锁存。参见[分频表与更新流程](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L982-L1060)及[共享 OPP 表](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/arch/riscv/boot/dts/espressif/esp32s31.dtsi#L103-L125)。
频率控制方法见[电源管理](../api-guides/power-management.md)。

## 定时器与外设输入时钟

| 提供者条目 / 定时器 | 本移植使用的频率 | 使用者 |
|---|---|---|
| `systimer` | 16 MHz | Linux 时间管理和每 CPU 定时事件 |
| 每个定时器组的定时器 1 | 40 MHz XTAL / 40 = 1 MHz | OpenSBI 空闲唤醒保护；不分配给 Linux GPTimer 驱动 |
| `uart0`–`uart3`、`i2c0`、`i2c1`、`ledc0`、`ledc1` | 提供者输入为 40 MHz | 外设驱动再配置波特率、总线或输出分频 |
| `gpspi2`、`gpspi3` | 提供者输入为 80 MHz | SPI 传输时钟分频器 |

外设输入时钟频率不等于最终的 UART 波特率、I2C/SPI 总线速率或 PWM 频率。参见[外设时钟注册](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L1635-L1747)及[保留的中断路由](interrupt-routing.md)。

驱动获取时钟的方法和 `clocks` 诊断属性统一见[时钟、复位与电源](../api-reference/system/clock-reset-power.md)。
