# 电源管理

本移植提供 CPU 频率控制、固件辅助空闲、诊断性 suspend-to-idle、保持路径，以及关机 / 深度睡眠请求。本指南介绍其控制方法及当前限制。

## CPU 频率

两个 HP 核共享一项频率策略，包含 80、160、240 和 320 MHz 工作点。读取可用频率和调频策略：

```sh
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_available_frequencies
cat /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
```

选择 userspace 调频策略并请求 160 MHz，数值单位为 kHz：

```sh
echo userspace > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
echo 160000 > /sys/devices/system/cpu/cpufreq/policy0/scaling_setspeed
```

恢复项目提供的默认策略：

```sh
echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor
```

Linux 时间管理使用独立的 16 MHz SYSTIMER。参见[时钟关系](../hw-reference/clock-tree.md)及[调频策略配置](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/configs/esp32s31_defconfig)。

## CPU 空闲

项目提供的命令行选择 `esp32s31_idle=wfi`。Linux 仅在所需 SBI 扩展存在时启用固件辅助 WFI 路径；关闭该选项或缺少该能力时，保留轮询回退路径。这是能力检查，不是对固件新旧的判断。参见[启用代码](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/irqchip/irq-esp32s31-smp.c)。

OpenSBI 保留每个定时器组的定时器 1 作为保护定时器，配置为 1 MHz 下的 10,000 个计数周期（10 ms）。`timers` 覆盖文件保留这些通道，仅向应用公开定时器 0。具体分配见[中断路由](../hw-reference/interrupt-routing.md)。

## 在 Linux 运行时测试 LP 唤醒处理

```sh
s31-lpctl ping
s31-lpctl sleep-test 1000
```

这些命令在 Linux 运行时检查邮箱与 LP 定时器。[LP 参考](../api-reference/lp-core/index.md)提供 GPIO 电平变化示例、参数范围和结果字段。测试系统睡眠前应先完成这些检查。

## 系统挂起前的准备

确认 LP 固件就绪。当前 SoftMAC 在 Wi-Fi 接口仍运行时返回 `EBUSY`，无线模块在停止蓝牙和共享载荷前返回该错误。进行 `freeze` 或 `mem` 实验前，先停止 Wi-Fi 活动并关闭接口，卸载 USB 文件系统并禁用 USB 存储上的 swap，因为设备可能重新连接。当前没有活动连接恢复实现，运行时重启不保证 Wi-Fi、蓝牙或组合模式自动重连。参见[无线架构](../api-reference/radio/architecture.md)。

## Suspend-to-idle（`freeze`）

LP 固件就绪后，启用一秒诊断定时器并进入 freeze：

```sh
echo 1000 > /sys/module/esp32s31_lp/parameters/s2idle_wake_ms
echo freeze > /sys/power/state
dmesg | tail -n 80
```

范围为 10–600000 ms；零（默认值）表示禁用自动定时器。验证在准备挂起时执行，因此参数写入被接受不代表请求的间隔有效。测试完成后，清除显式设置的测试定时器：

```sh
echo 0 > /sys/module/esp32s31_lp/parameters/s2idle_wake_ms
```

该路径测试 Linux 设备挂起 / 恢复和 LP 事务。HP 侧在 noirq 阶段轮询 LP 完成状态，因此不能据此证明 HP 进入了低功耗状态。参见[轮询实现](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c)。

S31 DWC2 挂起回调禁用自身 IRQ、控制器的全局中断使能及底层硬件，并设置 `phy_off_for_suspend`。这里不存在专门为 freeze 保持控制器 / PHY 活动的例外。恢复路径按需重新启用并恢复控制器，USB 设备可能重新连接。参见 [DWC2 挂起 / 恢复](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/usb/dwc2/platform.c)。

## Suspend-to-RAM（`mem` / `deep`）

当前 Linux / LP / OpenSBI 源码在 ABI 1 和 28 字控制块布局上保持一致。现有检查覆盖 ABI 版本一致性及 LP 定时器启动条件。参见[源码约定测试](https://github.com/GrieferPig/esp32-s31-linux/blob/main/tools/tests/test_s31_feature_contracts.py)及 [LP 开发指南](lp-firmware-development.md)。

`/sys/module/esp32s31_lp/parameters/` 下提供以下参数：

| 参数 | 接受的值 | 默认值 |
|---|---|---|
| `mem_wake_ms` | 定时器间隔，10–600000 ms | 2000 |
| `mem_wake_gpio` | LP GPIO0–7，或 `-1` 禁用 GPIO 唤醒 | `-1` |
| `mem_gpio_active_high` | `Y` 为高电平，`N` 为低电平 | `Y` |
| `mem_gpio_pull` | `0` 无，`1` 上拉，`2` 下拉 | `0` |

即使添加 GPIO 唤醒，也必须保留定时器作为恢复唤醒源。与运行状态下的 GPIO 测试一样，所选 GPIO 在 ARM 执行时必须处于非有效电平。LP 在 OpenSBI 发布 `HP_ASLEEP` 后启动保持定时器。相关配置与内存保留区见[电源域](../hw-reference/power-domains.md)及[内存映射](../hw-reference/memory-map.md)。

进行开发测试时，先查看运行内核公开的状态。只有列表中包含 `deep` 时，才继续执行下面的保持请求：

```sh
cat /sys/power/state
cat /sys/power/mem_sleep
```

```sh
echo 2000 > /sys/module/esp32s31_lp/parameters/mem_wake_ms
echo -1 > /sys/module/esp32s31_lp/parameters/mem_wake_gpio
echo deep > /sys/power/mem_sleep
echo mem > /sys/power/state
dmesg | tail -n 100
```

`mem_sleep` 决定 `mem` 的含义；`deep` 选择平台保持路径。参见 [Linux 挂起注册](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/arch/riscv/kernel/suspend.c)及 [MEM 请求验证](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c)。

## 关机

```sh
poweroff
```

Linux 停止服务并同步文件系统后，请求固件关机。时钟提供者在停止次级 hart 前准备好 40 MHz XTAL 交接；OpenSBI 在进入 PMU 流程前验证该状态。无定时唤醒的关机若无法完成，固件会停止执行而不重启。按 Reset/EN 或重新上电可再次启动 Linux。该命令不会切断板卡的外部电源。参见[时钟交接](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/clk/clk-esp32s31.c)及[固件回退](https://github.com/GrieferPig/opensbi-esp32-s31/blob/v1.9-esp32-s31/platform/generic/espressif/esp32s31/services.c)。

## 定时深度睡眠

定时深度睡眠请求有序关闭 Linux，随后执行**全新的冷启动**，不会保留正在运行的应用。请先保存应用状态。LP 固件就绪后，可请求四秒间隔：

```sh
for attr in /sys/bus/platform/devices/*/deep_sleep; do
    [ -w "$attr" ] || continue
    echo 4000 > "$attr"
    break
done
```

公开控制接受 1000–600000 ms，使用定时器唤醒源。Linux 锁存请求并发起有序关机；OpenSBI 配置 RTC 并选择冷启动路径。参见[请求处理](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c)及 [RTC 配置](https://github.com/GrieferPig/opensbi-esp32-s31/blob/v1.9-esp32-s31/platform/generic/espressif/esp32s31/services.c)。

RTC 换算使用固定的 **155386 Hz** 慢时钟值，因此不同板卡上的实际间隔可能不同。`previous` 和 `wake_reason` 是所请求操作的软件标记，不能证明物理睡眠成功。定时状态切换失败可能回退到复位；将一次重启认定为睡眠周期成功之前，应检查串口日志。

GPIO 唤醒已用于运行状态下的测试和保持请求，尚未用于公开的冷启动深度睡眠控制。此处未实现 LP-UART 和 WoWLAN 数据包唤醒路径。
