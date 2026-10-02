# 系统设置

打开 `esp32-config` 的 **System**，可修改主机名、登录密码、时间和开机程序。
以下命令均在开发板上以 root 身份运行。

## 主机名和登录密码

选择 **Hostname**，输入名称，再选择 **Save and apply**。
主机名立即生效，并在启动时恢复。也可以使用命令行：

```sh
esp32-config system hostname my-s31
```

选择 **Change login password** 可设置 root 账户的密码。
菜单会打开系统密码提示，要求输入两遍新密码。
修改后，开发板的登录服务使用新密码。对应命令为：

```sh
esp32-config system password
```

## 日期和时间

选择 **Date and time → Time zone and automatic time**。
选择已安装的时区，例如 `America/Los_Angeles` 或 `Asia/Shanghai`，
再选择是否使用网络时间服务器。系统会自动应用该时区的夏令时规则。

例如，选择洛杉矶时间并启用网络校时：

```sh
esp32-config system time configure America/Los_Angeles 1 pool.ntp.org
esp32-config system time status
```

参数分别为 `ZONE`、`AUTOMATIC`（`0` 或 `1`）和 `SERVER`。
默认时区是 `Etc/UTC`，自动校时初始为关闭。保存的设置会在启动时恢复。
自动校时需要可用的网络连接。

立即请求一次校时：

```sh
esp32-config system time sync
```

此操作最多等待 30 秒，并报告校时是否完成。启用时间服务本身不代表时钟已经同步。

离线使用时，选择 **Set date and time manually**，或运行：

```sh
esp32-config system time set '2026-09-26 12:00:00'
```

将示例替换为所选时区的当前本地时间。手动设置会关闭自动校时，
并修改运行中的时钟；断电后需要重新设置时间或启用网络校时。
保存的时区设置会保留。

## 开机运行程序

将可执行文件或可执行的 shell 脚本放到持久存储中。
例如，为已有脚本添加执行权限：

```sh
chmod +x /root/start-player.sh
```

选择 **Startup program → Program and arguments**，输入绝对路径，
再将每个参数各写在一行。参数按原样传递；管道、重定向和其他 shell 命令应写在脚本内。
选择 **Run at startup → Enabled**，让程序随 Linux 启动。

对应命令为：

```sh
esp32-config system autostart configure /root/start-player.sh
esp32-config system autostart enable
esp32-config system autostart start
esp32-config system autostart status
```

需要参数时，将它们放在 `configure` 后，按正常 shell 规则使用引号：

```sh
esp32-config system autostart configure /root/start-player.sh --volume 50
```

修改程序或开机开关不会重启正在运行的程序。
需要立即使用新设置时，先选择 **Stop program**，再选择 **Start saved program**。
即使没有启用开机运行，也可以单独启动一次已保存的程序。
关闭开机运行会保留当前实例；以下命令分别取消开机运行并停止当前程序：

```sh
esp32-config system autostart disable
esp32-config system autostart stop
```

程序以 root 身份运行，不接收控制台输入。
请让程序保持在前台运行，以便启动器跟踪退出状态并停止它。
每次启动只运行一次，退出后不会自动重启。
放在可移动存储上的应用需要对应存储卷先完成挂载。

页面显示当前运行状态和上次退出状态。也可以运行
`esp32-config system autostart status` 查看结果。
上次运行结果是临时数据，重启后清除；程序选择和参数会保留。

启动器会丢弃标准输出和标准错误。应用需要日志时，可在脚本中将输出写入合适的文件，
并限制日志大小。配置的备份方法见[配置](../resources/configuration.md)。
