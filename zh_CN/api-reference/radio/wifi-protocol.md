# Wi-Fi 协议与接口边界

当前 Linux Wi-Fi 前端使用 mac80211/cfg80211。用户空间通过 nl80211、`iw`、`wpa_supplicant` 和 `wpa_cli` 管理一个 STA 接口；应用数据通过普通网络套接字传输。

当前前端不注册向固件写入 EAP 凭据的 cfg80211 厂商命令。因此不要将固件中的 EAP 操作或主机辅助工具视为现成的企业认证接口。企业网络必须通过当前 Linux STA 栈和所选 `wpa_supplicant` 配置单独验证。AP 和 AP+STA 也不在当前前端公开的能力内。

## 无线桥接边界

| 项目 | 限制 |
|---|---:|
| 无线桥接帧 | 4144 字节 |
| 原始 SoftMAC 帧 | 4096 字节 |

共享类型和限制见当前源码中的 `linux-esp32-s31/include/linux/esp32s31-radio.h` 和 `include/linux/esp32s31-radio-control.h`。`receive_aux` 回调接收的是借用帧，存储只在回调期间有效；需要跨回调使用的数据必须先复制。前端通过 NAPI 将帧交给 mac80211，此路径可能使用原子分配。

当前扫描使用 mac80211 软件扫描，固件内部扫描 API 的 32 项数组不是当前 STA 扫描结果数量的上限。软件监听接口共用经过过滤的接收路径，不能提供完整混杂抓包。

配置方法见[Wi-Fi 与蓝牙设置](../../user-guides/networking.md)，功能范围及验证要求见[Wi-Fi 高级用法](../../api-guides/wifi-advanced.md)。
