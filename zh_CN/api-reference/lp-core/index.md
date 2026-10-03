# 低功耗核

`esp32s31_lp` remoteproc 驱动将固件加载到 LP SRAM，并通过硬件邮箱与 LP 核交换 32 位消息。常用固件名为 `esp32s31/s31-lp-core.elf`。启动和替换方法见 [LP 固件开发](../../api-guides/lp-firmware-development.md)。

## 检查启动与定时器

```sh
s31-lpctl status
s31-lpctl ping
s31-lpctl sleep-test 1000
```

收到 READY 后，`status` 包含 `ready=1`、最后一条消息及邮箱计数。`ping` 报告 `ready` 和 `rtt_us`；往返时间并不固定。`sleep-test` 接受 **10–5000 ms**，并设置 `DRY_RUN`，因此 Linux 保持运行。定时器测试成功时，`result=0`，且 `wake_reason` 包含定时器位（`0x1`）。参见[测试处理与结果格式](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c)。

## 测试 GPIO 电平变化

CLI 接受 LP GPIO0–7、电平 `low` 或 `high`、上下拉 `none`、`up` 或 `down`，以及 **10–5000 ms** 的超时（默认 1000 ms）。选择板上可用的引脚，并在 **ARM 执行时保持非有效电平**。

测试 GPIO3 高电平唤醒时，先保持输入为低电平，在完成布防后、1 秒超时前将它驱动为高电平：

```sh
s31-lpctl gpio-test 3 high down 1000
```

测试低电平唤醒时，先保持高电平，再将它驱动为低电平：

```sh
s31-lpctl gpio-test 3 low up 1000
```

固件配置上下拉后会等待 100 微秒，使输入稳定；若输入已经处于有效电平，则以 `S31_LP_SLEEP_ERR_WAKE_MASK` 拒绝请求。`DRY_RUN` 同样执行此检查。因此，不能仅将内部上下拉设置为有效电平来完成测试；外部电路或绑带也可能改变初始电平。参见 [ARM 验证](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/main/lp_core/main.c)。

GPIO3 测试成功时，`result=0`，`wake_reason` 包含 GPIO 位（`0x2`），`raw` 包含位 3（`0x8`）。超时意味着在指定时间内未完成有效的电平变化。Linux 始终保持运行；此测试通过不能证明系统挂起或深度睡眠唤醒可靠。

## 设备与属性

| 接口 | 说明 |
|---|---|
| `/dev/s31-lp` | 写入必须恰好为 4 字节；读取缓冲区至少为 4 字节，每次接收一个 32 位邮箱字 |
| `ready` | 是否已收到 READY 通知 |
| `last_message` | 最后收到的字 |
| `mailbox_stats` | 消息、确认及超时计数 |
| `tx_message` | 发送邮箱字 |
| `ping` | 启动或读取 PING/PONG 测试 |
| `sleep_test` | 启动或读取定时器测试 |
| `gpio_test` | 启动或读取 GPIO 测试 |
| `deep_sleep` | 读取深度睡眠标记或请求定时关机 |

这些属性属于已绑定的 LP 平台设备。固件选择与启停使用 remoteproc 的 `firmware` 和 `state` 属性。二进制读取可能阻塞等待消息；非阻塞读取在队列为空时返回 `-EAGAIN`。参见[字符设备实现](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c)。

## 邮箱与共享控制块

命令字的高 16 位表示操作，低 16 位表示序列号。READY（`0x53310001`）和 WAKE（`0x53310002`）是固定通知。除 PING/PONG 和 STATUS 外，协议还包含以下睡眠操作：

| 操作 | 用途 |
|---|---|
| PREPARE | 验证请求及所支持的唤醒配置 |
| ARM | 为事务及唤醒源布防，包括检查 GPIO 当前为非有效电平 |
| QUERY | 读取状态、结果、唤醒原因及时间戳 |
| RECLAIM | 将已完成事务的控制权交还 Linux |
| ABORT | 取消请求并解除唤醒源布防 |

共享块采用 **ABI 版本 1**，包含 **28 个紧凑排列的 32 位字（112 字节）**，地址为 `0x2E007C00`。LP SRAM 的最后 1 KiB 为它保留。Linux 与 LP 固件包含同一个协议定义；当前 OpenSBI 的验证也与该版本和布局一致。

| 字段组 | 单位 / 含义 |
|---|---|
| `deadline_lo`、`deadline_hi` | 一个以微秒为单位的相对时长，尽管字段名为 deadline |
| `sleep_ticks_lo`、`sleep_ticks_hi` | 定时器启动 / 事务布防时的绝对 RTC 计数值 |
| `wake_ticks_lo`、`wake_ticks_hi` | 记录唤醒时的绝对 RTC 计数值 |
| `state`、`result` | 事务状态和协议结果码 |
| `wake_reason`、`wake_raw` | 唤醒源掩码及源特定的原始位 |

保持（`MEM`）路径中，固件在 OpenSBI 发布 `HP_ASLEEP` 后启动定时器，不会在 Linux 较早的设备挂起阶段消耗这段时长。参见[定时器单位转换](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/main/lp_core/main.c)及[保持路径的启动条件](https://github.com/GrieferPig/esp32-s31-linux/blob/main/firmware/lp/main/lp_core/main.c)。

请求 CRC 覆盖 `request_crc` 前的字节；响应 CRC 覆盖 `response_crc` 前的字节，包括请求与结果字段。Linux 使用 `crc32_le(~0U, data, length) ^ ~0U`，并在 LP 发布响应期间重试快照读取。[协议头文件](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/include/linux/soc/espressif/esp32s31-lp-protocol.h)是消息码、标志、状态与字段的权威定义；[CRC 读取实现](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/drivers/remoteproc/esp32s31_lp.c)定义验证行为。

系统睡眠命令与验证边界见[电源管理](../../api-guides/power-management.md)。
