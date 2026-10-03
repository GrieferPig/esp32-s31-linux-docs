# esp32-config

在开发板控制台以 root 身份运行 `esp32-config`，打开配置菜单。
选择设置，编辑当前值，再保存并应用。**Back** 返回上一级，**Finish** 退出工具。
退出后，已提交的设置仍会保留。

## 菜单

| 页面 | 设置 |
|---|---|
| System | 主机名、登录密码、日期/时间、开机程序 |
| Network | Wi-Fi 网络、IPv4 地址、DNS |
| Bluetooth | 启用状态、设备名、已保存配对 |
| Interfaces | 外设选择、引脚、参数、GPIO、USB 功能 |
| Memory & storage | Swap 和一个可移动存储卷 |
| Maintenance | 导出、导入、重置、完整状态 |

页面根据运行镜像中安装的驱动和工具提供功能。例如，USB 设备功能需要 gadget 支持，
挂载存储卷需要对应的文件系统驱动。菜单开关无法启用镜像中未编译的驱动。
见[构建配置](../get-started/build-configuration.md)。

常规设置提交后生效。开机程序配置在下次启动该程序时使用。
导入或重置的设置在重启 Linux 后一起应用；这些操作会说明需要重启。

## 系统命令

```text
esp32-config system hostname [NAME]
esp32-config system password
esp32-config system time status|apply|sync
esp32-config system time configure ZONE AUTOMATIC SERVER
esp32-config system time set 'YYYY-MM-DD HH:MM:SS'
esp32-config system autostart status|enable|disable|start|stop
esp32-config system autostart configure EXECUTABLE [ARG ...]
```

`hostname` 省略 `NAME` 时会提示输入新名称。
`password` 打开系统密码工具，为 root 修改密码。
时间配置中的 `AUTOMATIC` 为 `0` 或 `1`。
`EXECUTABLE` 使用绝对路径，每个 `ARG` 按原样传递。
示例和启动行为见[系统设置](../user-guides/system-settings.md)。

## 网络命令

```text
esp32-config wifi status|scan|configure|enable|disable|forget
esp32-config wifi connect SSID [psk|open]
esp32-config wifi configure-hex SSID_HEX [psk|open]
esp32-config network status
esp32-config network dhcp [auto|manual [DNS ...]]
esp32-config network static ADDRESS PREFIX GATEWAY_OR_- [DNS ...]
```

交互式 `wifi configure` 要求输入一次 SSID 和一次密码，然后保存并连接。
`connect` 通过参数接收 SSID，从终端或标准输入读取一次密码。
选择 `open` 时不读取密码。`configure-hex` 接收以十六进制表示的完整 SSID 字节。

加密配置接受 8–63 字节的密码，或 64 位十六进制 PSK。
工具保存派生密钥，不保留明文口令。
加密网络的 SSID 包含零字节时，需要使用 `configure-hex` 和预先计算好的 PSK；
开放网络只需使用 `configure-hex`。

为兼容已有自动化，非交互式 `wifi configure` 保留三行输入约定：SSID、密码、相同密码。
该兼容流程只保存配置。新脚本可以使用 `wifi connect`，从标准输入提供一行密码，
完成保存并连接。

连接操作在完成后返回 `0`，应用失败时返回 `1`，等待结束但连接仍未完成时返回 `2`。
重试前可先查看 `wifi status`；等待未完成时，连接进程会继续运行。
参数用法错误也会返回非零状态。

地址命令接受 IPv4 地址和最多三个 DNS 服务器。不需要网关时使用 `-`。
修改地址设置会重新连接已启用的 Wi-Fi；Wi-Fi 关闭时，设置保留到下次连接使用。
见 [Wi-Fi 与蓝牙配置](../user-guides/networking.md)。

## 蓝牙命令

```text
esp32-config bluetooth info|status|enable|disable|restart
esp32-config bluetooth name [NAME]
esp32-config bluetooth clear-pairings
```

`name` 省略名称时显示保存的名称。名称为 1–29 字节，不能包含控制字符，默认为 `S31 Radio`。
启用蓝牙时修改名称会重启蓝牙。`clear-pairings` 清除当前控制器的 Classic 和 BLE 密钥，
并重启正在运行的蓝牙服务。

启用蓝牙会提供 Classic A2DP 传输和 BLE 外设功能。
内置应用没有用于 PCM 播放的音频解码器。
`bluetooth scan` 命令报告不支持扫描，菜单中没有扫描入口。

改变 Wi-Fi/蓝牙启用组合会重新加载共享无线模块。重复设置相同的启用状态不会执行重启；
需要恢复连接时，使用 `apply wifi` 或 `bluetooth restart`。
配对和服务说明见[网络指南](../user-guides/networking.md)。

## 接口与 GPIO

```text
esp32-config overlay COMMAND [ARG ...]
esp32-config gpio list|status|apply|reset
esp32-config gpio set LINE application|low|high
esp32-config gpio set LINE input [none|up|down]
esp32-config gpio read LINE
```

`overlay` 将参数转交给 [s31-overlay](overlay-catalog.md)，包括 `--volatile`。
接口页面分别读取默认值、当前值和保存值；固定引脚只显示，不提供 GPIO 编辑字段。

GPIO 配置立即生效，退出菜单后继续保持，并由 Linux 启动服务恢复。
`application` 释放引脚并移除保存配置。
`reset` 释放工具持有的全部 GPIO，并清除其保存配置。
`read` 读取受管理的输入；读取受管理的输出时，返回配置的电平。
使用方式和引脚占用规则见[使用外设](../user-guides/peripherals.md)。

原有诊断命令继续保留在 CLI 中：

```text
esp32-config gpio info [CHIP]
esp32-config gpio get CHIP LINE
esp32-config gpio pulse CHIP LINE VALUE [SECONDS]
```

`pulse` 临时输出 1–30 秒，默认为 3 秒。
它不创建保存配置，也不属于配置菜单。

## 内存、存储与 USB

```text
esp32-config storage status
esp32-config storage swap status|disable|apply|stop
esp32-config storage swap enable DEVICE
esp32-config storage configure DEVICE PATH AUTOSTART READONLY
esp32-config storage mount|unmount
esp32-config storage autostart 0|1
esp32-config usb status|apply|stop
esp32-config usb configure MODE [SERIAL_LOGIN [IP/PREFIX]]
```

存储命令选择已有的 swap 设备或文件系统，不会格式化设备。
设备可以用 `/dev/...` 路径或 `UUID=...` 标识。
`AUTOSTART` 和 `READONLY` 均为 `0` 或 `1`。
挂载目录应为 `/mnt` 或 `/media` 下的空目录。
见[内存与存储](../user-guides/memory-and-storage.md)。

USB 的 `MODE` 为 `host`、`serial` 或 `network`。
`SERIAL_LOGIN=0` 表示应用串口，`1` 表示 Linux 登录控制台。
网络模式使用 ECM，开发板地址默认为 `192.168.7.2/24`。
电脑端配置和角色切换方法见 [USB 功能](../user-guides/usb-gadget.md)。

## 应用设置与管理备份

```text
esp32-config status
esp32-config apply [all|system|wifi|bluetooth|gpio|storage|usb]
esp32-config stop
esp32-config maintenance backup PATH.tar
esp32-config maintenance restore PATH.tar
esp32-config maintenance reset network|bluetooth|interfaces|gpio|system|memory|all
```

`apply` 默认使用 `all`，重新应用系统、无线、GPIO、USB 和存储设置。
它不会启动开机程序，也不会替换当前活动的覆盖层集合。
`apply system` 应用主机名和时间设置。
`stop` 停止受管理的 Wi-Fi 连接，并保留保存的策略。

备份只包含 `esp32-config` 管理的设置。
导入和重置会保留用户程序、登录密码和蓝牙配对密钥。
重启 Linux 后应用导入或重置的配置。
备份示例、持久存储和恢复方法见[配置](configuration.md)。

## 持久化文件

| `/etc/esp32-conf` 下的文件 | 内容 |
|---|---|
| `system.conf` | 主机名 |
| `wifi.conf` | Wi-Fi 启用状态、接口、SSID 标识、IPv4/DNS 策略 |
| `wpa_supplicant.conf` | 保存的 STA 配置 |
| `bluetooth.conf` | 启用状态、控制器选择、BLE 策略、设备名 |
| `overlays.conf` | 保存的外设选择和参数 |
| `gpio.conf` | 受管理的 GPIO 配置 |
| `time.conf` | 时区、自动校时开关、时间服务器 |
| `autostart.conf`、`autostart.args` | 开机程序和按原样传递的参数 |
| `swap.conf` | Swap 设备选择和启动策略 |
| `storage.conf` | 存储卷、挂载路径、访问方式、启动策略 |
| `usb.conf` | USB 模式、串口登录选择、网络地址、设备标识 |

配置目录权限为 0700，设置文件权限为 0600。
登录密码由系统密码工具单独管理。
运行状态保存在 `/run/esp32-config`，重启后清除。

主入口位于 `buildroot-external/board/esp32-s31/overlay/usr/sbin/esp32-config`，
设置模块位于同一 overlay 下的 `usr/lib/esp32-config` 目录。
