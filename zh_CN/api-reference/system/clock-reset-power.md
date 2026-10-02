# 时钟、复位与电源

设备树引用将 S31 外设连接到 Linux 的时钟、复位和电源域提供者。[时钟树](../../hw-reference/clock-tree.md)说明已注册的时钟关系，[电源域](../../hw-reference/power-domains.md)说明各域的控制策略。

## 获取和释放驱动资源

通过提供者 API 获取设备绑定声明的资源。保留资源获取操作返回的错误，包括 `-EPROBE_DEFER`，使内核能在所需提供者就绪后重新尝试探测。

| API | 作用 |
|---|---|
| `devm_clk_get()` | 获取时钟引用，不会启用时钟 |
| `clk_prepare_enable()` | 准备并启用已获取的时钟 |
| `clk_get_rate()` | 读取用于计算外设时序的时钟频率 |
| `clk_disable_unprepare()` | 与成功的准备、启用操作配对 |
| `devm_reset_control_get_optional_exclusive()` | 获取可选复位控制；未提供可选控制时可能返回 `NULL` |
| `reset_control_reset()` | 通过该控制请求一次复位脉冲 |

S31 I2C 的探测流程可作为具体示例：映射寄存器，获取并启用时钟，通过 `devm_add_action_or_reset()` 注册 `clk_disable_unprepare()` 清理操作，获取并触发可选复位，然后配置控制器并申请 IRQ。错误路径保留提供者的错误码。这是该控制器的顺序；其他设备应遵循自身绑定与硬件要求。参见 [I2C 探测与清理](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/i2c/busses/i2c-esp32s31.c#L774-L830)。

释放时钟或缓冲区前，应停止设备传输与中断活动。DMA 清理还要求同步完成，见 [DMA 与缓存一致性](../../api-guides/dma-and-cache.md)。客户端驱动不应绕过提供者，直接写入时钟或 PMU 寄存器。

## 查看提供者状态

```sh
for file in /sys/bus/platform/devices/*/clocks; do
    [ -r "$file" ] && cat "$file"
done
for file in /sys/bus/platform/devices/*/domains; do
    [ -r "$file" ] && cat "$file"
done
```

`clocks` 的每一行包含以下字段：

| 字段 | 含义 |
|---|---|
| 开头的整数 | S31 时钟绑定中的时钟 ID |
| 名称 | 注册到 CCF 的时钟名称 |
| `state=on` / `state=off` | `clk_hw_is_prepared()` 的结果，即 CCF 准备状态 |
| `critical=0` / `critical=1` | CCF 是否将该时钟标记为关键时钟 |
| `rate=` | 提供者报告的频率，单位为 Hz |

`state=on` 不是对实际电气时钟信号的独立回读，也不能证明外设已正常工作。应结合频率、探测日志和设备状态解释该字段。具体输出格式见 [`clocks_show()`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/clk/clk-esp32s31.c#L1392-L1415)。

`domains` 输出分别列出策略、软件状态和强制控制寄存器设置；见[字段定义](../../hw-reference/power-domains.md)。CPU 频率与系统睡眠控制见[电源管理](../../api-guides/power-management.md)。
