# Wi-Fi 高级用法

当前镜像使用 mac80211 SoftMAC 前端，提供一个 2.4 GHz STA 接口。普通连接使用 `esp32-config`，并通过 `iw`、`wpa_cli` 和 `ip` 检查；参见[无线指南](../api-reference/radio/index.md)。固件中的某项操作或镜像包含的工具，并不意味着 Linux 前端已公开相应能力。

## 检查当前接口

在开发板上运行：

```sh
iw dev
iw phy
wpa_cli -p /run/wpa_supplicant -i wlan0 status
```

以实际启动内核的 `iw phy` 输出为准。当前驱动接受一个 STA 接口，拒绝额外的 STA 或 AP 接口。

## 监听接收

mac80211 可以提供软件监听接口，但当前无线接收路径仍采用面向 STA 的过滤，包括丢弃无关的单播帧。因此抓包不是完整的混杂信道视图。专用监听的验收和注入行为尚未确立，不能用未捕获到某个包来证明空中没有该包。

紧凑 rootfs 未选择 `tcpdump`。开发时可按[添加用户空间工具](adding-a-userspace-tool.md)加入抓包工具，但必须限制文件大小：`/tmp` 使用 RAM，persist 在扣除文件系统开销前只有 2120 KiB。较大的抓包应写入外接存储。

## 接入点模式

当前 SoftMAC 前端不公开 AP、AP+STA 或受保护 AP 模式。镜像已使用完整开发板配置，安装或运行 `hostapd` 不会增加 AP 支持。P4/C6 测试夹具仍可作为外部 AP，用于测试 S31 的 STA 功能。

## 企业认证

企业认证需要针对当前 Linux STA 栈和所选 `wpa_supplicant` 构建进行验证，本指南不声明端到端企业认证已受支持。开发集成时，应使用网络管理员提供的 CA 和服务器身份验证策略，不要为通过测试而关闭服务器验证。当前前端不公开用于向固件安装 EAP 凭据的厂商命令；接口边界见 [Wi-Fi 协议](../api-reference/radio/wifi-protocol.md)。

## 挂起与恢复

当前 SoftMAC 没有活动连接恢复功能。接口运行时，挂起辅助函数返回 `EBUSY`；无线模块会在挂起蓝牙或停止共享载荷之前返回该错误。实验系统休眠前应先关闭 Wi-Fi 接口。无线运行时重启不代表 STA 已重新关联。

HIL 的 `--wifi-suspend-cycles` 是诊断序列，不是恢复能力保证。测试系统休眠前，请阅读[电源管理](power-management.md)。
