# Wi-Fi 与蓝牙配置

在开发板控制台运行 `esp32-config`。**Network** 包含 Wi-Fi 和 IPv4 设置，
**Bluetooth** 包含蓝牙服务、设备名和配对管理。以下命令以 root 身份运行。
保存的设置会在启动时恢复；存储和备份方法见[配置](../resources/configuration.md)。

Wi-Fi 和蓝牙共用一个无线模块。改变启用的服务组合会重启该模块，可能中断两种连接。
重复选择已经保存的启用或关闭状态不会重启无线模块。
保持当前无线模式重新连接 Wi-Fi 时，不会重启蓝牙。

## 连接 Wi-Fi

1. 选择 **Network → Wi-Fi network → Connect / change network**。
2. 选择附近的网络；隐藏网络或手动输入 SSID 时，选择 **Enter network name**。
3. 对于加密网络，输入一次密码并选择 **Connect**。开放网络不需要输入密码。

网络选择会保存，并立即开始连接。提交前从输入页面返回，会保留原有配置。
Wi-Fi 页面显示选中的网络、连接状态和获得的 IPv4 地址。
选择 **Reconnect saved network** 可以使用已有密码重新连接。

配置页面支持开放网络和 WPA/WPA2 Personal。
加密网络接受 8–63 字节的密码，或 64 位十六进制 PSK。
包含空格、标点或非 ASCII 字符的网络名会按原样保存。
其他认证方式见[进阶 Wi-Fi](../api-guides/wifi-advanced.md)。

在交互式控制台中，可以用以下命令保存并连接：

```sh
esp32-config wifi configure
```

输入 SSID，再输入一次密码。也可以将网络名写在命令行中，密码仍在单独的提示中输入：

```sh
esp32-config wifi connect 'My Wi-Fi'
```

连接开放网络：

```sh
esp32-config wifi connect 'Guest Wi-Fi' open
```

## 检查连接或重试

```sh
esp32-config wifi status
esp32-config network status
```

连接完成需要 Wi-Fi 已关联，并获得 IPv4 地址。
如果等待结束时尚未完成，工具会说明设置已保存、连接仍在等待。
连接进程会继续运行，可以离开菜单，稍后再查看状态。
等待未完成本身不代表密码错误。

重试页面保留网络选择，提供 **Retry connection**、**Change password**、
**Choose another network** 和 **View details**。
也可以从命令行重新应用已保存的 Wi-Fi 配置：

```sh
esp32-config apply wifi
```

查看详细状态和日志：

```sh
wpa_cli -p /run/wpa_supplicant -i wlan0 status
cat /run/esp32-config/wpa_supplicant.log
cat /run/esp32-config/udhcpc.wlan0.log
```

DHCP 客户端持续运行，以获取和续租地址。
选择 **Forget saved network**，或运行 `esp32-config wifi forget`，可删除保存的网络并关闭 Wi-Fi。

## 设置 IPv4 地址和 DNS

选择 **Network → IP address and DNS**。默认通过 DHCP 自动获取地址和 DNS。
使用静态地址时，选择 **Manual**，填写地址和前缀；需要网关时再填写网关。
DNS 需手动指定；不需要 DNS 的本地网络可将列表留空。
完成后选择 **Save and apply**。修改正在使用的连接会重新连接 Wi-Fi；
Wi-Fi 关闭时，设置会在下次连接时应用。

例如，网络为 `192.168.1.0/24`，路由器和 DNS 服务器均为 `192.168.1.1`，
为开发板分配的空闲地址为 `192.168.1.50`：

```sh
esp32-config network static 192.168.1.50 24 192.168.1.1 192.168.1.1
```

请使用为实际网络分配的地址。参数分别为 `ADDRESS`、`PREFIX`、`GATEWAY` 和最多三个 DNS 地址。
不需要网关时使用 `-`。恢复自动地址和 DNS：

```sh
esp32-config network dhcp
```

也可以通过 DHCP 获取地址，同时指定自己的 DNS：

```sh
esp32-config network dhcp manual 192.168.1.1
```

DHCP 续租不会覆盖保存的手动 DNS 策略。这些设置用于受管理的 Wi-Fi 接口。
USB 网络使用独立的地址设置，见 [USB 功能](usb-gadget.md)。

## 使用内置蓝牙应用

启用蓝牙后，镜像通过 `/etc/init.d/S40btstack` 启动 `/usr/sbin/s31-btstack-a2dp`。这是一个使用 `/dev/s31-hci` 的 BTstack 主机，在同一进程中提供 Classic A2DP 接收端、AVRCP 支持和一个小型 BLE GATT 外设。

**[内置 A2DP 应用](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/package/btstack-s31/btstack-s31.mk)接收压缩的 SBC 媒体数据，用于传输测试。SBC 解码已在编译时移除，也没有 PCM 播放后端。** 因此，连接手机并启动媒体流后，会在日志中得到状态和数据包计数；要实际播放声音，还需要开发应用。

### 1. 启动蓝牙

```sh
esp32-config bluetooth enable
esp32-config bluetooth info
/etc/init.d/S40btstack status
cat /run/s31-btstack-a2dp.log
```

服务状态报告进程是否运行。控制器初始化、广播、配对和媒体流事件应通过日志检查。

### 2. 配对并发送 Classic 音频流

在手机或电脑上打开蓝牙设置，选择名称为 `S31 Radio` 的设备，或在 **Bluetooth → Device name** 中保存的名称。完成对端的配对提示，并将开发板选为音频输出设备。[内置示例](https://github.com/bluekitchen/btstack/blob/431d58d5613fd8fae38afe50282b25302de84bf7/example/a2dp_sink_demo.c#L678-L697)会自动接受 SSP 确认请求，并拒绝旧式 PIN 码配对。

在对端开始播放音频，然后暂停，再次查看服务日志。检查媒体流启动、暂停事件，以及媒体数据包和 SBC 字节计数。这些结果反映传输测试应用的接收情况。服务日志还会记录序列号缺口和重复数据包。

### 3. 读取 BLE 测试特征

在另一台设备上使用 BLE 中心设备或 GATT 查看应用。扫描配置的蓝牙名称（初始为 `S31 Radio`），连接后发现服务 `0xff10`，并读取特征 `0xff11`。它的值为文本 `ready`；该[测试特征](https://github.com/GrieferPig/esp32-s31-linux/blob/main/buildroot-external/package/btstack-s31/0013-a2dp-add-minimal-ble-gatt.patch)不要求配对。手机普通蓝牙设备列表可能不显示 GATT 外设，请使用 BLE 应用的扫描功能。

开发板上的 `esp32-config bluetooth scan` 命令会报告不支持扫描。内置主机提供外设角色；BLE 随 Classic 蓝牙一同启用。

## 修改蓝牙名称或清除配对

选择 **Bluetooth → Device name**，可以统一设置 Classic 蓝牙、BLE 扫描响应和
GAP Device Name 使用的名称。名称长度为 1–29 字节，不能包含控制字符。
UTF-8 名称中的一个字符可能占多个字节。例如：

```sh
esp32-config bluetooth name 'My S31'
```

蓝牙启用时，改名会重启蓝牙，并断开当前连接的设备；Wi-Fi 服务继续运行。

选择 **Clear saved pairings**，可清除当前控制器保存的 Classic 和 BLE 密钥。
蓝牙需要已经启用并正在运行。对应命令为：

```sh
esp32-config bluetooth clear-pairings
```

操作会重启蓝牙。重新配对前，请先在手机或电脑上移除旧配对。
如果已经保存启用设置，但服务启动失败，可选择 **Retry starting Bluetooth**，
或运行 `esp32-config bluetooth restart`；此恢复操作也可能重新连接 Wi-Fi。

## 停止、重启或交接控制器

| 任务 | 开发板命令 |
|---|---|
| 停止当前 Wi-Fi 连接，保留保存的策略 | `esp32-config stop` |
| 根据已保存配置重新启动 Wi-Fi | `esp32-config apply wifi` |
| 禁用 Wi-Fi，并在后续启动时保持禁用 | `esp32-config wifi disable` |
| 停止 BTstack，将 `/dev/s31-hci` 交给其他应用 | `/etc/init.d/S40btstack stop` |
| 在保存策略已启用时再次启动 BTstack | `/etc/init.d/S40btstack start` |
| 禁用蓝牙，并在后续启动时保持禁用 | `esp32-config bluetooth disable` |

其他程序打开 `/dev/s31-hci` 前，先停止 BTstack；该设备只允许一个客户端。重启服务前，先关闭自己的程序。[无线参考](../api-reference/radio/index.md)介绍了直接 HCI API、模块参数和 `radio_health` 诊断信息。

启动失败的排查方法见[调试](../api-guides/debugging.md)。配对数据和设置使用[配置](../resources/configuration.md)中介绍的存储方式；服务日志是临时文件。
