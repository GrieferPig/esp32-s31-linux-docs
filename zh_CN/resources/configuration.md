# 配置

在开发板上使用 `esp32-config` 配置常用设置：

```sh
esp32-config
```

菜单界面用于管理系统设置、网络、蓝牙、接口、GPIO 和内存/存储选择。保存的设置存储在
`/etc/esp32-conf` 中，由启动脚本应用。

## 选择配置位置

| 需要更改的内容 | 配置位置 |
|---|---|
| 加入驱动 | 内核 defconfig 和构建配置 |
| 加入应用程序 | Buildroot defconfig 或外部软件包 |
| 启用外设或更改其引脚 | `esp32-config` 的 Interfaces 或 `s31-overlay` |
| 配置 Wi-Fi、蓝牙、GPIO、开机程序或存储 | `esp32-config` |
| 更改 CPU 频率 | Linux cpufreq 接口 |
| 更改外设的运行时设置 | 对应的 Linux 子系统 API |
| 更改 flash 分区布局 | 布局配置、引导加载程序和设备树 |

构建时的配置选项见[构建配置](../get-started/build-configuration.md)。
运行时的外设选择见[使用覆盖层](overlay-catalog.md)。

## 持久化文件

根文件系统通过 OverlayFS 将只读 SquashFS 镜像与可写 JFFS2 层合并。
persist 成功挂载时，写入合并后根文件系统的普通文件会存入持久层，包括
`/etc/esp32-conf` 和 `/var/lib/btstack` 中的蓝牙配对数据。应用程序使用这些常规路径；
JFFS2 存储层在早期启动阶段完成挂载与组合。

以下位置用于临时存储：

| 路径 | 常见内容 |
|---|---|
| `/run` | 服务状态、进程 ID 和启动日志 |
| `/tmp` | 临时文件 |
| `/var/log` | 运行日志 |

持久化分区容量为 **2120 KiB**，其中一部分由文件系统元数据占用。当前布局没有专用 HIL 临时分区。
较大的应用程序、媒体文件和日志应存放在 SD 卡或 USB 存储设备上。
完整配置包含 FAT/VFAT 和内置 ext4；使用 SD 卡前，还需启用相应存储覆盖层。

部分由固件管理的文件会在启动时恢复为镜像中的版本。
这些例外及替换文件的安装方式见
[部署需要在重启后保留的文件](deploy-files-that-must-survive-reboot)。

## 更新时保留设置

仅当开发板已使用相同紧凑布局时，完整匹配组件烧录或 `make flash-existing-all` 才能保留 persist。该目标不会构建，应先运行 `make image`。更换布局必须先备份并全新安装。烧录 `s31_full_flash.bin` 或擦除整个芯片都会替换已保存的数据。
见[烧录与首次启动](../get-started/flash-and-first-boot.md)。

## 备份与恢复设置

选择 **Maintenance → Export configuration**，输入一个新的 `.tar` 文件名。
要将备份放到[已挂载的可移动存储](../user-guides/memory-and-storage.md)上：

```sh
esp32-config maintenance backup /mnt/media/esp32-config-backup.tar
```

备份包含配置工具管理的设置，以及已保存的 Wi-Fi 凭据。
请妥善保管，并在擦除 flash 前将备份复制到板外。
用户程序、登录密码、蓝牙配对密钥和已挂载存储中的文件不包含在备份中。
工具不会覆盖已有备份文件。

通过 **Maintenance → Import configuration** 导入，或运行：

```sh
esp32-config maintenance restore /mnt/media/esp32-config-backup.tar
```

工具先检查归档和配置内容，再替换已保存的设置。
导入会恢复 `esp32-config` 管理的完整配置快照，不会逐字段合并现有设置。
用户文件会保留。重启 Linux 后，恢复的设置一起生效；
导入时不会立即停止当前程序、释放 GPIO 或断开网络。

## 重置配置

选择 **Maintenance → Reset configuration**，再选择设置组，或使用：

```text
esp32-config maintenance reset network|bluetooth|interfaces|gpio|system|memory|all
```

每次提供一个组名。例如，仅重置已保存的网络设置：

```sh
esp32-config maintenance reset network
```

默认设置在重启 Linux 后生效。重置 `system` 或 `all` 会保留登录密码。
蓝牙配对密钥也会保留；需要删除时，使用[清除已保存配对](../user-guides/networking.md)。
重置配置不会删除用户程序和其他文件。

## 无线设置

无线模式在模块加载时选择。模块参数 `mode` 和 `direct_hci` 分别选择 Wi-Fi/蓝牙组合与蓝牙前端。XIP 加载器读取烧入专用 Flash 分区的预链接无线镜像，不按文件名加载，也没有 `firmware` 参数。日常设置应使用配置工具；如需更改这些模块参数，
应先停止无线应用程序，再重新加载模块。

参数值和 Linux 接口见[无线参考](../api-reference/radio/index.md)。

## 无法保存设置时

通过 `df -h`、`/proc/mounts` 和 `dmesg` 检查可用空间及存储错误。
正常启动后，根文件系统应为可写的 OverlayFS。如果早期启动无法找到或挂载 persist、
构建 OverlayFS，或切换到合并后的根文件系统，就会输出错误并启动只读 SquashFS 基础系统。
在可写存储恢复之前，配置将无法保存。

修改覆盖层后，应在 `s31-overlay status` 中同时检查当前生效和预期保存的条目。
保存失败、替换回滚及恢复已保存选择的行为见[使用覆盖层](overlay-catalog.md)。
