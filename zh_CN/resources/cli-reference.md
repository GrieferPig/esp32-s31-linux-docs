# 命令行参考

除非某一节明确要求在主机上运行，否则以下命令均在开发板的 Linux 控制台中执行。
构建和烧录命令见 [Make 参考](make-reference.md)。

## esp32-config

```sh
esp32-config
```

打开开发板配置菜单，用于配置系统、网络、蓝牙、接口、GPIO、内存/存储和配置备份。
命令和配置步骤见 [esp32-config](esp32-config.md)。

## s31-overlay

```text
s31-overlay list
s31-overlay status
s31-overlay routes NAME
s31-overlay parameters NAME
s31-overlay describe NAME
s31-overlay check CONFIG_FILE
s31-overlay apply NAME [KEY=VALUE ...] [--volatile]
s31-overlay remove NAME [--volatile]
s31-overlay remove --all [--volatile]
s31-overlay restore
```

`list` 显示已安装的覆盖层；`status` 显示当前生效和已保存的集合。
`routes` 和 `parameters` 显示覆盖层的默认值和可选项。
`describe` 以制表符分隔的记录分别显示默认值、当前值和保存值。
`check` 根据已安装的覆盖层目录检查保存配置，不会应用它。

`apply` 和 `remove` 默认更新指定名称的保存选择；`remove --all` 清空保存集合。
使用 `--volatile` 可保持已保存的选择不变。保存文件存在时，`restore` 会用已保存条目替换当前生效的集合。
示例和失败行为见[使用覆盖层](overlay-catalog.md)。

## s31-lpctl

```text
s31-lpctl status
s31-lpctl ping
s31-lpctl sleep-test MS
s31-lpctl gpio-test PIN low|high [none|up|down] [MS]
s31-lpctl send WORD
s31-lpctl recv
```

| 命令 | 说明 |
|---|---|
| `status` | 显示固件就绪状态、邮箱计数器和 ping 状态 |
| `ping` | 请求一次 PING/PONG 交互 |
| `sleep-test` | 在 Linux 保持运行的情况下执行 10–5000 ms 的 LP 定时器测试 |
| `gpio-test` | 测试 LP GPIO0–7 的电平，可选择上拉或下拉，并设置 10–5000 ms 的超时时间 |
| `send` | 发送一个 32 位邮箱字 |
| `recv` | 等待一个邮箱字，并以十六进制输出 |

GPIO 测试默认不启用上拉或下拉，超时时间为 1000 ms。指定超时时间前，必须先提供上下拉设置参数。
例如：

```sh
s31-lpctl gpio-test 3 high up 500
```

配置方法和协议详情见 [LP 核](../api-reference/lp-core/index.md)。

## s31-selftest

```text
s31-selftest [--quick|--stress] [--json] [--duration SECONDS]
             [--require-radio-traffic]
```

默认的快速测试检查系统健康状态，并执行少量持久化写入测试。
压力模式增加并行的 CPU、XIP 读取、持久化写入和无线健康检查。
默认持续时间为 60 秒，可设置为 10–3600 秒。

```sh
s31-selftest --quick
s31-selftest --stress --duration 60 --json
```

`--json` 每行输出一条 JSON 结果。在压力模式下，`--require-radio-traffic` 会将
Wi-Fi/蓝牙数据包计数器没有变化的情况判为失败；测试期间应产生相应的流量。

## s31-modload

```text
s31-modload MODULE.ko [PARAM=VALUE ...]
s31-modload --remove MODULE_NAME
```

加载内核模块（包括 XZ 压缩的模块），或按内核模块名移除模块。
正常的无线启动由开发板的服务脚本负责。开发模块时，可在停止使用该设备的应用程序后使用此工具。

## HIL（硬件在环）工具

这些工具用于自动执行 ESP32-S31 平台的硬件在环测试。

在主机上运行以下命令，查看测试运行器的选项：

```sh
python3 tools/hil/s31_hil.py --help
```

运行器协调 S31 上的 `s31-hil-agent` 和可选的对端固件。
完整命令和测试装置配置见[硬件在环测试](../contribute/testing-hil.md)。

## Wi-Fi 诊断

```sh
iw dev
iw phy
wpa_cli -i wlan0 status
ip addr show wlan0
```

当前 mac80211 SoftMAC 前端只提供一个 STA，不公开固件 EAP 凭据厂商命令。AP、监听及企业认证限制见[Wi-Fi 高级用法](../api-guides/wifi-advanced.md)。

## 开发工具

项目包含 CoreMark、内存和 libc 测试、扩展指令测试及其他诊断工具的源码。
其中有多个工具会被 `post-build.sh` 从精简 rootfs 中移除。
如需将工具加入镜像，请参照[添加用户空间工具](../api-guides/adding-a-userspace-tool.md)。
