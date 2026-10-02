# Wi-Fi 高级用法

驱动提供 STA、接入点和监听接口，每种类型最多一个，共享同一个 2.4 GHz 信道。普通开放网络或 PSK STA 设置见 [Wi-Fi 与蓝牙设置](../user-guides/networking.md)。

监听接收可以直接通过 `iw` 操作。AP 认证和企业网络关联还需要在普通配置向导之外完成集成，具体范围见下文。

## 监听接收

加载 Wi-Fi 无线模块后，在开发板上停止受管理的 STA 连接：

```sh
esp32-config stop
```

选择信道前，还应停止所有 AP 管理程序。创建只接收的监听接口：

```sh
iw dev wlan0 interface add mon0 type monitor
ip link set mon0 up
iw dev mon0 set channel 6 HT20
```

设置信道时，STA 必须已断开，AP 必须已停止。如果 STA 或 AP 正在工作，监听接收会使用它们的信道。接收的数据包包含带有信道和信号信息的 radiotap 头部。不支持数据包注入。

要保存抓包结果，先[将 `tcpdump` 加入镜像](adding-a-userspace-tool.md)，然后在开发板上运行：

```sh
tcpdump -i mon0 -s 0 -w /tmp/capture.pcap
```

`/tmp` 使用 RAM，因此应控制抓包文件大小，或选择已挂载的外接存储上的文件。按 Ctrl+C 停止抓包，移除接口，并按需恢复已保存的 STA 连接：

```sh
iw dev mon0 del
esp32-config apply wifi
```

## 接入点集成

在开发板上运行以下命令创建 AP 接口：

```sh
iw dev wlan0 interface add ap0 type __ap
ip link set ap0 up
```

接下来需要 AP 管理程序启动接入点，并配置 IP 地址、DHCP 服务器和路由。镜像选择了 `hostapd`，但本移植项目的驱动要求 AP 启动请求携带 WPA2 PSK 或 WPA3 SAE 密码，以便将认证卸载到固件。这里尚未建立适用于该路径的完整可用 `hostapd` 配置。仅创建 `ap0` 不会启动接入点。

[驱动](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/net/wireless/espressif/esp32s31_wifi.c#L702-L750)验证以下设置，并向固件请求最多四个客户端：

| 设置 | 接受的值 |
|---|---|
| 安全模式 | 开放、WPA2-PSK 或 WPA3-SAE |
| 受保护网络的加密算法 | CCMP |
| 信道宽度 | 20 MHz |
| 向固件请求的最大客户端数 | 4 |
| 信标间隔 | 100–60000 TU |
| DTIM 周期 | 1–10 |
| SAE 密码 | 1–63 字节 |

这些是软件限制；固件和连接的客户端是否接受各个极限值，需要集成测试。请选择一种认证方式，不支持混合 WPA2/WPA3 过渡模式。使用 AP+STA 时，先启动 AP，再让 STA 连接同一信道。AP 重新配置会在固件中停止并重启 Wi-Fi，可能中断 STA 连接。

## 企业网络凭据配置

固件实现 PEAP 和 EAP-TLS 认证。主机工具 [tools/s31_wifi_eap.py](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/tools/s31_wifi_eap.py) 用于配置身份、CA 证书、服务器域名，以及用户凭据或客户端证书。该流程只安装凭据，不会关联 SSID 或获取 IP 地址。

### 1. 准备主机配置文件

对于 PEAP，在电脑上创建 `profile.json`：

```json
{
  "identity": "anonymous@example.invalid",
  "username": "user@example.invalid",
  "password_file": "password.txt",
  "ca_file": "ca.pem",
  "domain": "radius.example.invalid"
}
```

使用网络管理员提供的身份、CA 和服务器域名。文件路径相对于 JSON 文件。密码文件的内容会原样使用，包括末尾换行符。请妥善保管这些文件。

对于 EAP-TLS，用 `cert_file` 和 `key_file` 替代用户名/密码组合。两种模式都必须提供身份、CA 和域名。每个字段最多 4095 字节，域名最多 253 字节；工具会拒绝内嵌 NUL 字节。

### 2. 准备访问方式并写入凭据

工具会在本机或通过 SSH 将二进制输入发送给 `iw`。以下主机示例要求开发板镜像已添加 SSH 服务器，且连接可用；默认镜像提供串口控制台，没有 SSH 服务器。若要直接在开发板上运行工具，还需将 Python 加入镜像。

更改凭据前，断开 STA 并停止自动重连。对于 `esp32-config` 管理的连接，在开发板上运行 `esp32-config stop`。如果停止 Wi-Fi 会断开 SSH，请使用另一条访问路径。PEAP 和 EAP-TLS 认证前都应正确设置开发板时钟：固件在两种模式下都启用了[证书时间检查](https://github.com/GrieferPig/esp32-s31-linux/blob/a6b62c6426f06f00ff3be7ee8e6ab1c67a1ff104/firmware/radio/radio_stack.c#L1426-L1444)。

将 `BOARD` 替换为可访问的 SSH 地址，在电脑上运行：

```sh
python3 tools/s31_wifi_eap.py --ssh root@BOARD profile.json
```

工具会清除旧配置，传输各字段，再提交新配置。凭据数据通过标准输入传递，而不是命令行参数。断开 STA 后，可用以下命令清除凭据：

```sh
python3 tools/s31_wifi_eap.py --ssh root@BOARD --clear
```

传输失败时，工具会尝试清除配置。如果已失去开发板访问连接，请恢复访问并清除配置后再重试。

### 3. 集成关联流程

接下来需要 STA 管理程序在写入凭据后，通过驱动的连接路径提交企业网络 SSID。普通 `wpa_supplicant` WPA-EAP 设置不会填充此固件配置，而 `esp32-config` 配置页面写入的是开放网络或 PSK 配置。本指南尚未提供完整集成的企业网络连接命令。添加该集成时，请在目标网络上验证关联、证书检查和 IP 数据传输。

自行开发配置客户端时，可参阅 [EAP 厂商协议](../api-reference/radio/wifi-protocol.md)中的数据包格式。

## 挂起后

恢复时，驱动会尝试恢复内存中保存的 EAP 字段、活动 AP 配置和运行中的监听接口。STA 会收到断开通知，由用户空间重新连接。恢复后应检查服务状态和网络数据传输；重启无线模块并不保证对端会重新连接。当前系统休眠限制见[电源管理](power-management.md)。
