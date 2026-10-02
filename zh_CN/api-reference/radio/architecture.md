# 无线架构

Wi-Fi 和蓝牙共享 `esp32s31-radio` Linux 模块。模块包含 Linux 前端、外部固件加载器，以及供乐鑫无线代码使用的运行时。

| 应用路径 | 公共模块中的前端 |
|---|---|
| 使用套接字的 Wi-Fi 应用 | cfg80211 和 netdev |
| 内置 BTstack 应用 | `/dev/s31-hci` 直接 H4 设备 |
| 替代的 Linux 蓝牙主机 | 使用 `direct_hci=0` 的 Linux HCI 控制器 |

三条路径都连接到同一个无线运行时和外部固件。帧格式、设备归属和模块设置见[无线接口参考](index.md)。

## 固件加载

ESP-IDF 库和本移植项目的兼容代码被链接成 `esp32s31-radio-fw-v1.o`，这是一个可重定位的 RISC-V ELF 目标文件。构建过程将它与匹配的模块一起打包到 `radio.sqfs`。

启动时，[加载器](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-loader.c)分配固件内存、解析导入符号、应用重定位，并查找导出入口。它在启动运行时之前检查载荷格式和 ABI。请使用同一次构建生成的固件和模块：ABI 编号相同，并不能保证每个私有导入项都兼容。

已加载固件的内存，包括可变数据段，与运行时使用的固定内部 SRAM 池相互独立。[分配辅助函数](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-loader-core.c)和[内存映射](../../hw-reference/memory-map.md)介绍了这两类分配。

## 运行时与 CPU 分配

主无线工作线程和硬件中断处理运行在 HP 核心 0。Wi-Fi 前端将接收 NAPI 和缓冲区补充工作调度到 HP 核心 1。[Wi-Fi 接收路径](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/net/wireless/espressif/esp32s31_wifi.c)通过这种分工，与无线运行时并行处理接收数据包。

兼容层提供无线库所需的任务、队列、定时器和同步功能。[任务创建适配层](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-rtos.c)在绑定任务的 Linux kthread 时，会遵循有效的核心请求；主工作线程位于 CPU0，并不表示所有载荷创建的任务都被绑定到 CPU0。

运行在中断上下文中的回调将数据复制到预分配的存储中，并调度后续工作。应用通过网络或蓝牙接口访问功能，无需直接调用固件。

## 挂起和恢复

挂起时，模块解除前端连接，停止运行时，并释放电源请求。恢复时，它还原固件初始可变数据，重启运行时，再恢复前端。如果重启失败，接口会保持断开，并记录错误。此流程由[模块的电源管理回调](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-module.c)实现。

Wi-Fi 前端恢复缓存的 EAP 字段、活动 AP 配置和运行中的监听接口。STA 连接需要用户空间重新建立。蓝牙前端会将控制器复位报告给已打开的直接 HCI 客户端，内置 BTstack 的复位处理程序会重新启动 HCI 状态机。原有无线连接仍需与对端重新建立。

连接检查和服务控制见 [Wi-Fi 与蓝牙设置](../../user-guides/networking.md)。系统休眠的可用情况见[电源管理](../../api-guides/power-management.md)。代码修改见[无线固件开发](../../api-guides/radio-payload-development.md)。
