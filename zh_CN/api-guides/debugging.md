# 调试

先查看串口控制台和 `dmesg`。结合两者可以查看引导程序输出、驱动信息，以及 Linux 运行时的错误信息。

当前合并镜像尚未重新进行模拟器运行或物理开发板启动、烧录验证。构建成功不代表这些运行路径已通过；请保留镜像标识及完整日志作为验证依据。

## 查看日志

以 115200 波特率、8N1 连接 UART0，然后运行：

```sh
dmesg
```

服务启动信息单独保存在以下文件中：

```sh
cat /run/rcS.log
test -e /run/rcS.done && cat /run/rcS.status
```

服务与登录控制台并行启动。启动脚本执行完毕后，会出现 `/run/rcS.done` 文件。如果刚登录时找不到某个设备，请检查启动过程是否仍在进行。

复位开发板前，请将有用的日志复制到电脑；重启会清空 `/run` 和内核日志。

## 检查系统

以下命令可以帮助了解系统概况：

```sh
uname -a
cat /sys/devices/system/cpu/online
cat /proc/meminfo
cat /proc/interrupts
cat /proc/mtd
cat /proc/mounts
s31-overlay status
```

`online` 通常显示 `0-1`。中断计数有助于判断设备是否产生中断。`/proc/mounts` 会显示可写的根文件系统覆盖层和已连接的存储设备。

## 常见问题

### 开发板无法启动

检查电源、USB 线、串口和启动模式按钮。使用 `esptool` 前，关闭其他串口监视程序。烧录后，复位开发板，使其进入正常启动模式。

如果控制台输出停在 ROM 或 SPL 阶段，检查引导程序镜像和 Flash 偏移。如果 Linux 已启动但无法挂载根文件系统，检查 DTB、内核和根文件系统镜像。[烧录与首次启动](../get-started/flash-and-first-boot.md)中的命令会将这些镜像写入预期位置。

从复位开始记录输出，并根据最后完成的启动阶段选择下一项检查。以下信息可用于判断进度：

| 输出 | 能确认的进度 | 下一项检查 |
|---|---|---|
| `ESP32-S31 SPL active` | SPL 已进入开发板初始化 | 阅读后续的内存和镜像加载信息；见[启动过程](../api-reference/system/boot-chain.md)。 |
| `S31 overlay: failed to mount persist as JFFS2` | Linux 已进入早期用户空间，但无法挂载可写存储 | 参照[配置](../resources/configuration.md)。 |
| `S31 early overlay restore failed` | 恢复已保存的设备树覆盖层时返回错误 | 按[使用覆盖层](../resources/overlay-catalog.md)检查当前覆盖层和保存选择。 |
| 串口登录提示符 | Linux 已启动控制台登录服务 | 检查 `/run/rcS.log` 和 `/run/rcS.done`，确认是否还有服务正在启动。 |

### 重启后设置丢失

通过 `df -h`、`/proc/mounts` 和启动日志检查存储错误。
持久化规则、容量和只读回退行为见[配置](../resources/configuration.md)。
如果只有覆盖层选择丢失，请比较 `s31-overlay status` 中的 `active:` 和 `persisted:` 条目。

### 找不到外设

运行 `s31-overlay status`，确认外设对应的覆盖层已激活。然后查看 `dmesg`，检查是否有 probe 失败，或缺少时钟、DMA 通道等依赖。完整[构建配置](../get-started/build-configuration.md)已包含原生可选驱动；定制内核还应核对最终配置。

### 覆盖层命令失败

查看错误信息、`s31-overlay status` 和 `dmesg`。某个 GPIO 或控制器可能已被其他覆盖层或应用占用。更改路由前，应先停止占用它的使用方。

重试前，请同时检查当前生效和已保存的条目。
各类错误的检查方法，包括保存失败和替换回滚，见[使用覆盖层](../resources/overlay-catalog.md)。

### Wi-Fi 或蓝牙无法启动

先检查服务状态：

```sh
esp32-config wifi status
esp32-config bluetooth info
```

查看 `dmesg` 中的固件加载错误，以及无线驱动 `radio_health` 属性中的初始化结果。
模块已加载时，仍可能存在设备 probe 失败或前端缺失的情况。
读取健康状态的方法见[无线参考](../api-reference/radio/index.md)。

对于 Wi-Fi，还应检查 `iw dev` 和 `wpa_cli -i wlan0 status`。
如果关联已完成，但 DHCP 仍未完成，请查看 `/run/esp32-config/udhcpc.wlan0.log`。
常规连接步骤见[网络配置](../user-guides/networking.md)。

### LP 命令失败

运行 `s31-lpctl status`。如果驱动不存在，检查 `lp` 覆盖层或内核配置；如果显示 `ready=0`，检查固件启动情况。查看 `dmesg` 中的固件加载和邮箱错误。挂起问题见[电源管理](power-management.md)。

## 报告问题

提供失败的命令、预期结果和相关控制台输出，并附上开发板型号、构建或发布版本，以及构建配置。外设问题还应说明接线和连接的设备。分享日志前，请移除敏感信息。
