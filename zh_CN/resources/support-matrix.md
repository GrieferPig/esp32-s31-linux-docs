# 功能支持

本页分别说明实现和构建中的可用情况，以及已有报告中的硬件测试范围。
可选总线、音频、存储和网络驱动需要使用
[完整外设配置](../get-started/build-profiles.md)构建。

## 可用状态

| 标记 | 含义 |
|---|---|
| 🟢 默认包含 | 默认构建已选择此功能所需的支持；使用时可能仍需配置 |
| 🟡 已实现 | 已有驱动或协议实现；备注列出仍需完成的配置或验证 |
| 🟠 开发中 | 集成或硬件验证尚未完成 |
| 🔴 未提供 | 本仓库未提供相应的 ESP32-S31 实现 |

这些标记描述[构建配置](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/Makefile#L283-L395)
和驱动支持情况。硬件测试报告及其覆盖范围列在后文。

## 系统

| 功能 | 可用状态 | 备注 |
|---|---|---|
| Linux、Sv32 MMU 和 flash XIP | 🟢 默认包含 | 按 16 MiB flash 和 16 MiB PSRAM 配置 |
| 双核 SMP | 🟢 默认包含 | 两个 HP hart 均配置为运行 Linux |
| 持久化根文件系统 | 🟢 默认包含 | SquashFS 配合 JFFS2 可写层 |
| 运行时覆盖层 | 🟢 默认包含 | 外设选择、引脚路由和设置保存 |
| CPU 动态调频 | 🟢 默认包含 | 共享的 80、160、240 和 320 MHz 策略 |
| CPU 空闲 | 🟢 默认包含 | 固件辅助的 WFI |
| LP 固件和邮箱 | 🟡 已实现 | remoteproc、PING/PONG、定时器和 GPIO 诊断 |
| Suspend-to-idle | 🟡 已实现 | LP 定时唤醒诊断使用 HP CPU 轮询 |
| 定时深度休眠 | 🟡 已实现 | 定时唤醒使用冷启动路径 |
| 正常关机 | 🟡 已实现 | 不设置定时唤醒；通过外部复位或重新上电启动 |
| Suspend-to-RAM 和 LP GPIO 唤醒 | 🟠 开发中 | 已有定时/GPIO 唤醒路径；验收仍需覆盖状态保持、唤醒原因及设备恢复 |

Linux、LP 固件和 OpenSBI 中的休眠协议定义现已一致。此前记录的协议不匹配
问题已在源码中解决。Suspend-to-RAM 和 LP GPIO 唤醒的开发板验证仍待完成。
本页未提供开发板电流测量结果。命令和唤醒源设置见
[电源管理](../api-guides/power-management.md)。源码参考：
[Linux 休眠结构](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/include/linux/soc/espressif/esp32s31-lp-protocol.h#L87-L117)、
[OpenSBI 检查](https://github.com/GrieferPig/opensbi-esp32-s31/blob/af2ff7c9c263bf474b0add45f614893e36d89814/platform/generic/espressif/esp32s31/services.c#L730-L748)。

## 无线

| 功能 | 可用状态 | 备注 |
|---|---|---|
| Wi-Fi STA | 🟢 默认包含 | cfg80211、`iw` 和 `wpa_supplicant` |
| 蓝牙 | 🟢 默认包含 | BTstack 配合直接 HCI；另有 Linux HCI 前端可选 |
| AP 和 AP+STA | 🟡 已实现 | AP 和 STA 共用一个信道；开放 AP 的历史报告见后文 |
| 加密 AP | 🟡 已实现 | 已有固件 PSK/SAE 卸载；仍需完整的 hostapd 配置及验收结果 |
| 企业认证凭据 | 🟠 开发中 | 已实现凭据传输；端到端企业认证仍需验收 |

提供的根文件系统使用 BTstack。尝试使用 BlueZ 还需要选择 Linux HCI 前端，
并修改 rootfs 软件包及 post-build 设置：当前 post-build 脚本会删除 BlueZ、
D-Bus 及相关库文件。仅选择 BlueZ 软件包并不足够。本页未验证完整的 BlueZ
配置流程。见 [post-build 删除规则](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/board/esp32-s31/post-build.sh#L174-L204)。

可用的配置方式见 [Wi-Fi 与蓝牙](../api-reference/radio/index.md)和
[进阶 Wi-Fi](../api-guides/wifi-advanced.md)。

## 外设

| 功能 | 可用状态 | 备注 |
|---|---|---|
| GPIO 和 UART0 控制台 | 🟢 默认包含 | GPIO 字符设备及 UART0 控制台 |
| 可选 UART | 🟡 已实现 | UART1/2 路由及 UART3 DMA；预置 UART3 HIL 用例使用内部回环 |
| I2C0/I2C1 | 🟡 已实现 | 已实现长传输分批处理；请验证应用所用的传输长度和设备 |
| GPSPI2/GPSPI3 主机 | 🟡 已实现 | 8 位字；数据线设置取决于控制器及所选设备 |
| GPSPI 目标端 | 🟡 已实现 | DMA 传输最长 4096 字节 |
| I2S/TDM | 🟡 已实现 | 播放/采集和可配置帧格式；预置覆盖层使用外部 BCLK/WS |
| SD/MMC | 🟡 已实现 | 插槽接线和总线宽度由覆盖层选择；卡和模式的覆盖范围需要测试装置结果 |
| 以太网 | 🟡 已实现 | 需要匹配的外部 PHY 配置和接线 |
| USB gadget | 🟡 已实现 | 需要完整外设构建并配置 gadget 功能；不在标准 HIL 测试范围内 |
| USB 主机 | 🟢 默认包含 | 默认选择主机控制器及存储支持；设备互操作性仍在开发验证中 |
| AHB/AXI GDMA | 🟡 已实现 | 由外设驱动使用；AXI GDMA 需要完整外设构建 |
| 定时器、PWM 和脉冲计数器 | 🟡 已实现 | 每个定时器组的定时器 1 为 CPU 空闲功能保留 |
| 模拟和传感器模块 | 🟡 已实现 | ADC、DAC、触摸和比较器通过 IIO 提供接口；温度通过 hwmon 提供接口；精度和校准需单独验证 |
| 看门狗、NVMEM、RNG 和加密 | 🟡 已实现 | 已接入各自的 Linux 子系统；仍需分别进行功能验收 |
| TWAI/CAN | 🟠 开发中 | 已有 SocketCAN 绑定和覆盖层；开发板/总线验收尚未完成 |
| RMT | 🔴 未提供 | 仓库中没有 ESP32-S31 的驱动或设备树节点 |

配置方法见[使用外设](../user-guides/peripherals.md)，API 设置和传输限制见
[外设参考](../api-reference/peripherals/index.md)，默认 GPIO 分配见
[模组和开发板](../hw-reference/modules-and-boards.md)。
[覆盖层目录](overlay-catalog.md)列出可选控制器。

## 测试和历史报告

项目提供主机测试及开发板/对端测试程序。HIL 的 `usb-drive` 用例覆盖 USB 主机
存储，不覆盖 gadget 功能或全部 USB 设备类别。命令、测试装置配置和结果收集
见 [HIL 测试](../contribute/testing-hil.md)。

以下报告保留自项目文档。这些条目均未链接包含测试日期、镜像标识和完整测试
装置记录的原始运行结果。与新结果比较时，请保留其原有范围。

| 接口 | 报告中的范围 | 来源和限制 |
|---|---|---|
| I2S0/I2S1 | 8、16 和 48 kHz 下的 S16_LE 立体声 | 未注明日期的 [HIL README 报告](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/hil/README.md#L90-L96)。仅检查有限的播放/采集窗口；未证明长时间稳定性或其他 DAI 格式 |
| SPI 目标端 | 模式 0–3；100 kHz 下按 MSB 优先顺序进行的 8、16、32 位传输，长度最高 4096 字节 | 未注明日期的早期功能支持表报告。当前标准 HIL 程序选择 8 位传输；报告中的 16/32 位用例需要单独保留结果 |
| 开放 AP | 已进行数据传输测试 | 未注明日期的早期功能支持表报告；该声明未附测试装置、镜像和流量覆盖范围 |

新的验收结果应记录镜像/提交、开发板和模组版本、测试接线、传输设置、结果及
清理证据。失败和跳过的用例也应保留。需要保存的内容见
[HIL 结果说明](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/hil/README.md#L145-L150)。

### Flash 和持久化存储

早期文档报告过影响设置保存或启动的 NOR 编程和 JFFS2 故障。要确定某个镜像
是否仍受影响，需要当前的复现记录。驱动现在已串行化 flash 访问，并与另一个
hart 协调；仅凭旧的故障提示无法判断新故障的原因。

报告故障时，请附上启动日志，以及出现的
`esp32s31-flash: ROM ... failed` 或
`S31 overlay: failed to mount persist as JFFS2` 消息，同时记录镜像标识和触发
故障的操作。这些消息分别来自当前的
[flash 错误路径](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/mtd/devices/esp32s31_flash.c#L130-L138)
和[根文件系统挂载错误](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/buildroot-external/board/esp32-s31/overlay/init#L44-L55)。
