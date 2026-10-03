# 功能支持

所有镜像使用[完整开发板配置](../get-started/build-configuration.md)。

## 可用状态

| 标记 | 含义 |
|---|---|
| 🟢 默认包含 | 默认构建已选择此功能所需的支持；使用时可能仍需配置 |
| 🟡 已实现 | 已有驱动或协议实现 |
| 🟠 开发中 | 集成尚未完成 |
| 🔴 未提供 | 本仓库未提供相应的 ESP32-S31 实现 |

这些标记描述[构建配置](../get-started/build-configuration.md)和驱动支持情况。

## 系统

| 功能 | 可用状态 | 备注 |
|---|---|---|
| Linux、Sv32 MMU 和 flash XIP | 🟢 默认包含 | 按 16 MiB flash 和 16 MiB PSRAM 配置 |
| 双核 SMP | 🟢 默认包含 | 两个 HP hart 均配置为运行 Linux |
| 持久化根文件系统 | 🟢 默认包含 | SquashFS 配合 JFFS2 可写层 |
| 可移动存储与 swap | 🟢 默认包含 | FAT/VFAT、内置 ext4、SD/MMC、USB 存储和 swap |
| 运行时覆盖层 | 🟢 默认包含 | 外设选择、引脚路由和设置保存 |
| CPU 动态调频 | 🟢 默认包含 | 共享的 80、160、240 和 320 MHz 策略 |
| CPU 空闲 | 🟢 默认包含 | 固件辅助的 WFI |
| LP 固件和邮箱 | 🟡 已实现 | remoteproc、PING/PONG、定时器和 GPIO 诊断 |
| Suspend-to-idle | 🟡 已实现 | LP 定时唤醒诊断使用 HP CPU 轮询 |
| 定时深度休眠 | 🟡 已实现 | 定时唤醒使用冷启动路径 |
| 正常关机 | 🟡 已实现 | 不设置定时唤醒；通过外部复位或重新上电启动 |
| Suspend-to-RAM 和 LP GPIO 唤醒 | 🟡 已实现 | 已有定时/GPIO 唤醒路径 |

Linux、LP 固件和 OpenSBI 使用一致的休眠协议定义。命令和唤醒源设置见
[电源管理](../api-guides/power-management.md)。源码参考：
[Linux 休眠结构](https://github.com/GrieferPig/linux-esp32-s31/blob/v6.18-esp32-s31/include/linux/soc/espressif/esp32s31-lp-protocol.h)、
[OpenSBI 检查](https://github.com/GrieferPig/opensbi-esp32-s31/blob/v1.9-esp32-s31/platform/generic/espressif/esp32s31/services.c)。

## 无线

| 功能 | 可用状态 | 备注 |
|---|---|---|
| Wi-Fi STA | 🟢 默认包含 | mac80211/cfg80211 单 STA；`iw`、`wpa_supplicant` |
| 蓝牙 | 🟢 默认包含 | BTstack 配合直接 HCI；另有 Linux HCI 前端可选 |
| AP、AP+STA 和受保护 AP | 🔴 未提供 | 当前 SoftMAC 前端不公开这些模式 |
| 软件监听 | 🟠 开发中 | 共用 STA 过滤接收路径，不是完整混杂捕获 |
| 企业认证 | 🟠 开发中 | 没有 EAP 厂商凭据接口 |
| 活动 Wi-Fi 挂起 | 🔴 未提供 | 接口运行时返回 `EBUSY`，没有活动连接恢复实现 |

提供的根文件系统使用 BTstack。尝试使用 BlueZ 还需要选择 Linux HCI 前端，
并修改 rootfs 软件包及 post-build 设置：当前 post-build 脚本会删除 BlueZ、
D-Bus 及相关库文件。仅选择 BlueZ 软件包并不足够。见 [post-build 删除规则](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/board/esp32-s31/post-build.sh)。

可用的配置方式见 [Wi-Fi 与蓝牙](../api-reference/radio/index.md)和
[进阶 Wi-Fi](../api-guides/wifi-advanced.md)。

## 外设

| 功能 | 可用状态 | 备注 |
|---|---|---|
| GPIO 和 UART0 控制台 | 🟢 默认包含 | GPIO 字符设备及 UART0 控制台 |
| 可选 UART | 🟡 已实现 | UART1/2 路由及 UART3 DMA；预置 UART3 HIL 用例使用内部回环 |
| I2C0/I2C1 | 🟡 已实现 | 已实现长传输分批处理 |
| GPSPI2/GPSPI3 主机 | 🟡 已实现 | 8 位字；数据线设置取决于控制器及所选设备 |
| GPSPI 目标端 | 🟡 已实现 | DMA 传输最长 4096 字节 |
| I2S/TDM | 🟡 已实现 | 播放/采集和可配置帧格式；预置覆盖层使用外部 BCLK/WS |
| SD/MMC | 🟡 已实现 | 插槽接线和总线宽度由覆盖层选择 |
| 以太网 | 🟡 已实现 | 需要匹配的外部 PHY 配置和接线 |
| USB gadget | 🟡 已实现 | 标准内核包含 ACM/ECM configfs 支持；运行时需选择功能；不在标准 HIL 测试范围内 |
| USB 主机 | 🟢 默认包含 | 默认选择主机控制器及存储支持 |
| AHB/AXI GDMA | 🟡 已实现 | 两个 DMA 提供者均已内置，由相应外设驱动使用 |
| 定时器、PWM 和脉冲计数器 | 🟡 已实现 | 每个定时器组的定时器 1 为 CPU 空闲功能保留 |
| 模拟和传感器模块 | 🟡 已实现 | ADC、DAC、触摸和比较器通过 IIO 提供接口；温度通过 hwmon 提供接口 |
| 看门狗、NVMEM、RNG 和加密 | 🟡 已实现 | 已接入各自的 Linux 子系统 |
| TWAI/CAN | 🟡 已实现 | 已有 SocketCAN 绑定和覆盖层 |
| RMT | 🔴 未提供 | 仓库中没有 ESP32-S31 的驱动或设备树节点 |

配置方法见[使用外设](../user-guides/peripherals.md)，API 设置和传输限制见
[外设参考](../api-reference/peripherals/index.md)，默认 GPIO 分配见
[模组和开发板](../hw-reference/modules-and-boards.md)。
[覆盖层目录](overlay-catalog.md)列出可选控制器。

## 测试

项目提供主机检查与开发板/对端测试程序。HIL 的 `usb-drive` 覆盖 USB 主机存储，不代表 gadget 或全部 USB 类别均受支持。命令、夹具及结果收集见[HIL 测试](../contribute/testing-hil.md)。

验收记录应包含镜像/提交标识、开发板和模组版本、接线、传输设置、命令、PASS/FAIL/SKIP 结果，以及恢复和清理证据。无线数据传输须记录对端，休眠结论须记录唤醒原因及电流。

### Flash 与持久化存储

当前布局的 persist 为 2120 KiB，内核和 rootfs 各为 6 MiB，没有 HIL 临时分区。固件更新应使用同布局的完整匹配集；更换布局先备份并重新安装。

发生 NOR 或 JFFS2 错误时，请保存完整启动日志、镜像标识和触发操作。`esp32s31-flash: ROM ... failed` 与 `S31 overlay: failed to mount persist as JFFS2` 分别指向 Flash 操作和 persist 挂载失败。根文件系统处于只读恢复环境时，不能承诺设置会保存。排查方法见[调试](../api-guides/debugging.md)。
