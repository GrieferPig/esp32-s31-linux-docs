# Wi-Fi 和蓝牙

ESP32-S31 无线模块提供 cfg80211 Wi-Fi 接口和蓝牙控制器。配置、配对、服务控制和连接检查见 [Wi-Fi 与蓝牙设置](../../user-guides/networking.md)。本页介绍应用接口和模块参数。

## Wi-Fi

网络接口通常为 `wlan0`；镜像包含 `iw`、`wpa_supplicant` 和 `wpa_cli`。应用数据通过普通网络套接字传输。[Wi-Fi 高级用法](../../api-guides/wifi-advanced.md)介绍了监听接收及 AP/企业网络集成路径。[EAP 厂商协议](wifi-protocol.md)定义了固件企业认证所用的凭据配置接口。

## 蓝牙

内置 BTstack 应用使用 `/dev/s31-hci`。加载模块时改用 `direct_hci=0`，会提供 Linux HCI 控制器。基于 BlueZ 的镜像还需要保留其守护进程、工具、依赖和服务配置：`post-build.sh` 会显式移除 BlueZ、D-Bus/GLib 和 BlueALSA 文件，仅选中软件包并不足够。构建这种替代方案时，请检查[运行文件精简规则](runtime-pruning)，并在更改控制器归属前停止直接 HCI 服务。

### 直接 HCI 设备

`/dev/s31-hci` 同时只允许一个应用打开，权限为 `0600`。其他应用使用此
设备之前，请先停止 BTstack。

一次写入发送一个完整的 H4 包：一个包类型字节，后跟 HCI 包数据。
接受的写入大小为 2–1,029 字节。

传给 `read()` 的大小决定接收格式：

| 请求读取大小 | 返回的数据 |
|---|---|
| 2–1,029 字节 | 一个完整的 H4 帧 |
| 大于 1,029 字节 | 最多八帧，每帧前带有一个两字节的小端长度字段 |

简单客户端可使用 1,029 字节的读取缓冲区。在批量模式中，每个长度都包含
H4 包类型字节。当缓冲区已满、已复制八帧或队列变空时，读取结束。

如果缓冲区不足以容纳下一帧，且尚未复制任何帧，则返回 `EMSGSIZE`。
从空队列进行非阻塞读取会返回 `EAGAIN`。使用 `poll()` 等待接收数据或
发送队列出现可用空间。

控制器重启后，已打开设备的客户端可能收到 HCI Hardware Error 事件。
此时应重新初始化主机并重新连接设备。关闭设备会释放主机端点，控制器
仍保持启用。[HCI 前端](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/bluetooth/hci_esp32s31.c)实现了此帧格式和生命周期。

## 模块设置

模块文件名为 `esp32s31-radio.ko`。在 Linux 中，它以 `esp32s31_radio`
的名称出现在 `/sys/module` 下。

| 参数 | 默认值 | 说明 |
|---|---|---|
| `mode` | `combo` | 启用 `wifi`、`bt` 或 `combo` |
| `direct_hci` | `1` | 提供 `/dev/s31-hci`；设为 `0` 则使用 Linux HCI |
| `firmware` | `esp32s31-radio-fw-v1.o` | 无线固件文件名 |

这些设置在加载模块时选定。常规模式选择使用 `esp32-config`；底层应用
应在更改模块配置前停止客户端。[模块实现](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/platform/esp32s31-radio-module.c)定义了模式和直接 HCI 的默认值。

(radio-status)=
## 无线状态

`radio_health` 属性报告初始化结果、堆使用量、数据包计数和工作线程活动：

```sh
for file in /sys/bus/platform/devices/*/radio_health; do
    [ -r "$file" ] && cat "$file"
done
```

无线服务无法启动或停止响应时，结合 `dmesg` 查看这些信息。

## 内核接口

公共无线 API 声明在
[`include/linux/esp32s31-radio.h`](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/include/linux/esp32s31-radio.h)
中，定义了前端使用的 Wi-Fi 和 HCI 回调。核心代码和外部载荷目前使用 ABI
版本 1。

| 项目 | 限制 |
|---|---:|
| HCI 帧 | 1,029 字节 |
| Wi-Fi 以太网帧 | 1,600 字节 |
| 扫描结果 | 32 个接入点 |

站点接收复制回调可能在硬中断上下文中运行，并使用预分配的缓冲区。
数据包处理由另一个回调调度。监听流量使用独立的接收路径。

```{toctree}
:maxdepth: 1

architecture
wifi-protocol
```
