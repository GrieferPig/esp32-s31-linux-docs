# 使用覆盖层

设备树覆盖层（overlay）用于启用可选外设并选择引脚。
在 `esp32-config` 的 **Interfaces** 中选择接口，编辑引脚和参数。
页面分别显示当前启用状态和保存的启动选择；字段值不同时，会标出保存值。
**Unavailable** 表示无法读取当前状态。已启用的接口可以直接编辑；固定引脚只显示，不能修改。

选择 **Enabled** 后显示参数字段，再选择 **Save and apply** 更新接口和启动选择。
保存 **Disabled** 会删除该接口的保存配置。
如果提交值与当前值和保存值都相同，接口会继续运行，不会重新应用。

脚本可以通过 `s31-overlay` 命令完成覆盖层操作。

## 列出可用的覆盖层

```sh
s31-overlay list
s31-overlay status
```

`list` 显示镜像中已安装的覆盖层。在 `status` 输出中，`active:` 条目来自运行中的内核，
`persisted:` 列出为下次启动保存的预期选择。
可选外设驱动已包含在统一的[完整配置](../get-started/build-configuration.md)中，仍需配置覆盖层与实际硬件。

| 分组 | 覆盖层名称 | 备注 |
|---|---|---|
| UART | `uart1`, `uart2`, `uart3`, `uart3-dma` | DMA 使用 UHCI0 和 AHB GDMA 通道对 0 |
| I2C | `i2c0`, `i2c1` | 独立的控制器及 SCL/SDA 路由 |
| SPI | `gpspi2`, `gpspi2-target`, `gpspi3`, `gpspi3-target` | 为各控制器选择主机或目标端模式 |
| 音频 | `i2s0`, `i2s1` | I2S 控制器和音频路由 |
| CAN | `twai0`, `twai1` | 需要外部 CAN 收发器 |
| SD/MMC | `sdmmc0`, `sdmmc1`, `sdmmc-dual`, `sdmmc-uhs` | 各变体共享 SD/MMC 主机 |
| 以太网 | `gmac` | 外部 PHY 和 RGMII 接线 |
| USB | `usb-device` | 将 USB OTG 控制器切换到设备模式 |
| 定时器 | `timers` | 提供每个定时器组中的定时器 0 |
| PWM/计数器 | `pwm-counter` | PWM 和脉冲计数器模块 |
| 模拟 | `analog` | 模拟模块及其焊盘选择 |
| 看门狗 | `watchdogs` | 看门狗模块 |
| DMA | `gdma` | AHB GDMA 通道对 4 |
| 无线 | `radio-wifi`, `radio-bluetooth`, `radio-combo` | 选择一个无线覆盖层 |
| LP 核 | `lp` | LP remoteproc 和邮箱 |

## 应用覆盖层

使用默认设置启用 I2C0：

```sh
s31-overlay apply i2c0
```

工具会立即应用覆盖层，并保存该名称对应的选择。
如需临时更改并保留原有保存设置，可添加 `--volatile`：

```sh
s31-overlay apply i2c0 --volatile
```

使用 `status` 检查结果，然后通过该外设的 Linux 接口使用它。

## 选择引脚和参数

先查看可用设置：

```sh
s31-overlay routes i2c0
s31-overlay parameters i2c0
s31-overlay describe i2c0
```

`routes` 和 `parameters` 显示已安装覆盖层的默认值与可选项。
`describe` 以制表符分隔的记录分别显示默认值、当前值和保存值。
如果无法确定活动覆盖层的当前参数，`current_known` 为 `0`，当前值字段显示 `-`。
固定 GPIO 声明以 `fixed_gpio` 记录显示。
无法读取当前引脚值时，菜单会要求先关闭该接口，再重新配置。

例如，使用 GPIO35 作为 SCL、GPIO36 作为 SDA，并将总线频率设为 400 kHz：

```sh
s31-overlay apply i2c0 i2c0.scl=35 i2c0.sda=36 clock-frequency=400000
```

路由键由覆盖层定义。标准目录提供以下数值参数：

| 覆盖层 | 参数 | 允许的值 |
|---|---|---|
| `i2c0`, `i2c1` | `clock-frequency` | `100000`, `400000`, `1000000` |
| SD/MMC 变体 | `bus-width` | `1`, `4` |

管理器检查 GPIO、输入路由、控制器或 DMA 资源是否冲突。flash 和控制台引脚已预留。
连接外部设备前应检查的事项及默认路由见[开发板指南](../hw-reference/modules-and-boards.md)。

## 移除或恢复覆盖层

关闭使用该外设的应用程序，然后移除其覆盖层：

```sh
s31-overlay remove i2c0
```

覆盖层已经停用时，此命令仍可清除它的保存选择。

使用 `remove --all` 移除所有受管理的覆盖层。命令成功后，对当前状态和保存设置的影响如下：

| 命令 | 当前生效的覆盖层 | 保存的选择 |
|---|---|---|
| `apply NAME` | 应用或替换 `NAME` | 仅添加或替换 `NAME` 条目 |
| `remove NAME` | 移除 `NAME` | 仅移除 `NAME` 条目 |
| `remove --all` | 移除所有受管理的覆盖层 | 清空所有已保存条目 |
| 为以上命令添加 `--volatile` | 执行相同的运行时更改 | 保持已保存条目不变 |

后续的常规命令会保留其他已保存条目。例如，先通过 `--volatile` 应用 `uart1`，
再正常应用 `uart2`，只会保存对 `uart2` 的更改。
反过来，通过 `--volatile` 移除已保存的覆盖层，也会保留其下次启动时的选择。

保存的覆盖层会在启动时自动恢复。如需手动重新加载该集合，运行：

```sh
s31-overlay restore
```

保存文件存在且可读时，`restore` 会移除当前集合并应用已保存的条目，从而中断涉及的外设。
空文件会清空当前集合。文件不存在时，命令成功返回并保持当前覆盖层不变；
文件格式错误或不可读时，会在更改当前覆盖层之前停止。

要根据已安装的覆盖层目录检查配置文件，并保持硬件不变，可运行
`s31-overlay check /etc/esp32-conf/overlays.conf`。该命令校验文件、覆盖层名称和参数；
实际应用时再检查当前的引脚和资源冲突。

USB 角色切换还会重新启动 USB 控制器；应先卸载已连接的 USB 存储设备，并禁用位于 USB 上的 swap。

## 保存的设置与故障排查

覆盖层通过 `/dev/s31-overlay` 加载。覆盖层文件存储在 `/usr/lib/s31-overlays` 下，
保存的设置位于 `/etc/esp32-conf/overlays.conf`。
CLI 将运行时选择记录在 `/run/s31-overlay.current` 中；`status` 则向内核查询当前生效的集合。
存储容量和文件保留规则见[配置](configuration.md)。

操作失败时，请检查错误信息、`s31-overlay status` 和 `dmesg`：

| 故障 | 检查事项 |
|---|---|
| 准备持久化集合失败 | 检查保存文件的语法和可读性。命令会在更改当前覆盖层之前停止。 |
| 替换当前覆盖层失败 | 内核会尝试重新应用原有覆盖层。如果回滚也失败，原有覆盖层将丢失；请在 `dmesg` 中查找回滚错误。 |
| `overlay applied, but recording state failed` 或对应的移除错误 | 硬件更改已经发生。分别检查当前状态和保存设置，解决存储错误后，再次执行所需命令。 |
| `restore` 应用某个条目时失败 | CLI 会尝试移除已恢复的部分集合。它不会重建执行 `restore` 前的集合；继续操作前应检查当前生效的覆盖层。 |

保存文件无法读取或解析时，也会显示 `persisted: (none)`。
如果已保存的选择意外从状态输出中消失，请检查 `/etc/esp32-conf/overlays.conf`，
并参照[配置](configuration.md)中的存储检查步骤。
