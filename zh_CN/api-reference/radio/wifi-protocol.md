# EAP 厂商协议

此接口为固件内的 EAP 客户端配置凭据。主机工具和配置文件格式见 [Wi-Fi 高级用法](../../api-guides/wifi-advanced.md)。凭据配置与 STA 关联是两个独立操作。

## 传输与请求布局

在 STA 接口上发送 cfg80211 厂商命令，使用厂商 ID `0x18fe34` 和子命令 `0x1`。辅助工具将每条二进制请求传递给：

```sh
iw dev wlan0 vendor send 0x18fe34 0x1 -
```

请求包含 20 字节头部，后跟字段数据。所有头部成员都是无符号小端 32 位整数；长度和偏移均以字节计。

| 字节偏移 | 成员 | 含义 |
|---:|---|---|
| 0 | operation | WRITE = 6，COMMIT = 7，CLEAR = 8 |
| 4 | field | WRITE 的字段 ID；其他操作为零 |
| 8 | offset | 本块在字段中的位置；其他操作为零 |
| 12 | total | WRITE 的完整字段长度；其他操作为零 |
| 16 | length | 头部后的数据字节数；COMMIT/CLEAR 为零 |
| 20 | data | WRITE 最多携带 512 字节 |

完整消息必须恰好包含 `20 + length` 字节。WRITE 要求分块非空，字段总长度为 1–4095 字节。

## 字段 ID

| ID | 字段 |
|---:|---|
| 0 | 身份 |
| 1 | 用户名 |
| 2 | 密码 |
| 3 | CA 证书 |
| 4 | 服务器域名 |
| 5 | 客户端证书 |
| 6 | 私钥 |

服务器域名最多 253 字节，且不能包含 NUL。提供的 Python 辅助工具还会拒绝其他所有字段中的 NUL。身份、CA 和域名为必填项；PEAP 还需提供用户名和密码，EAP-TLS 则需同时提供客户端证书和私钥。

## 事务顺序

1. 断开 STA 并停止自动重连。
2. 发送 CLEAR，其余头部成员全部为零。
3. 各字段从偏移零开始，按连续分块写入。同一字段的 `total` 保持不变。所有字段完成后再发送 COMMIT。
4. 发送 COMMIT，其余头部成员全部为零。提交成功后，驱动后续的 STA 连接调用就会使用企业网络凭据。

STA 处于已连接、连接中或挂起状态，或者命令发给其他接口时，驱动会拒绝凭据配置。未清除字段就再次从偏移零开始写入，会返回 `EALREADY`。大小错误、分块乱序、字段不完整，以及 COMMIT 后继续写入，都会被拒绝。失败后应先清除部分配置，再重试；辅助工具会自动尝试清理。

凭据保存在运行时内存中。驱动可以在挂起/恢复周期后重新写入凭据；重启或移除模块后则需再次配置。关联和 IP 配置仍由 STA 管理程序完成。

## 实现

[控制头文件](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/include/linux/esp32s31-radio-control.h)定义操作和字段 ID。[Wi-Fi 前端](https://github.com/GrieferPig/linux-esp32-s31/blob/bd15992071dc9496b9f14b5a765dfa23a71d289b/drivers/net/wireless/espressif/esp32s31_wifi.c)验证请求，并缓存字段供恢复时使用。`tools/tests/test_s31_feature_contracts.py` 使用 `tools/s31_wifi_eap.py` 测试主机端序列化和失败清理。
